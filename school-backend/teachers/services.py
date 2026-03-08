from django.db.models import Avg, Count, Case, When, IntegerField, F, Q
from academics.models import ExamResult, GradebookEntry, TeacherAssignment

class TeacherAnalyticsService:
    @staticmethod
    def get_teacher_performance_overview(teacher):
        """
        Returns a high-level performance overview for a specific teacher.
        """
        # 1. Total Students Taught (Distinct)
        assignments = TeacherAssignment.objects.filter(teacher=teacher)
        classrooms = assignments.values_list('classroom_id', flat=True)
        
        # 2. Subject Averages (Current Session)
        results = ExamResult.objects.filter(
            subject__teacher_assignments__teacher=teacher,
            exam__school=teacher.school
        )
        
        avg_score = results.aggregate(avg=Avg(F('marks_obtained') / F('max_marks') * 100))['avg'] or 0
        
        # 3. Pass Percentage
        # Define pass as >= 35%
        pass_count = results.filter(marks_obtained__gte=F('max_marks') * 0.35).count()
        total_results = results.count()
        pass_rate = (pass_count / total_results * 100) if total_results > 0 else 0
        
        return {
            "average_score": round(float(avg_score), 1),
            "pass_percentage": round(float(pass_rate), 1),
            "total_evaluations": total_results,
            "classes_assigned": classrooms.count()
        }

    @staticmethod
    def get_grade_distribution(teacher):
        """
        Returns grade distribution (A, B, C, D, F) for the teacher's students.
        """
        results = ExamResult.objects.filter(
            subject__teacher_assignments__teacher=teacher
        )
        
        distribution = results.annotate(
            percentage=F('marks_obtained') / F('max_marks') * 100
        ).aggregate(
            A=Count(Case(When(percentage__gte=80, then=1), output_field=IntegerField())),
            B=Count(Case(When(Q(percentage__gte=60) & Q(percentage__lt=80), then=1), output_field=IntegerField())),
            C=Count(Case(When(Q(percentage__gte=40) & Q(percentage__lt=60), then=1), output_field=IntegerField())),
            F=Count(Case(When(percentage__lt=40, then=1), output_field=IntegerField())),
        )
        
        return {
            "labels": ["A (80%+)", "B (60-80%)", "C (40-60%)", "F (<40%)"],
            "data": [distribution['A'], distribution['B'], distribution['C'], distribution['F']]
        }

    @staticmethod
    def get_class_performance_trend(teacher):
        """
        Returns performance trend across different classrooms managed by the teacher.
        """
        assignments = TeacherAssignment.objects.filter(teacher=teacher).select_related('classroom', 'subject')
        
        trends = []
        for assign in assignments:
            avg = ExamResult.objects.filter(
                classroom=assign.classroom,
                subject=assign.subject
            ).aggregate(avg=Avg(F('marks_obtained') / F('max_marks') * 100))['avg'] or 0
            
            trends.append({
                "classroom": str(assign.classroom),
                "subject": assign.subject.name,
                "average": round(float(avg), 1)
            })
            
        return trends
