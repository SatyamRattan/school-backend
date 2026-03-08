from fpdf import FPDF
from io import BytesIO

class ReportCardPDF(FPDF):
    def __init__(self, school_name="School Management System"):
        super().__init__()
        self.school_name = school_name

    def header(self):
        self.set_font('helvetica', 'B', 20)
        self.cell(0, 10, self.school_name, align='C')
        self.ln(15)
        self.set_font('helvetica', 'B', 14)
        self.cell(0, 10, 'Student Report Card', align='C')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')

def generate_report_card_pdf(student, exam_results, school_name="My School"):
    pdf = ReportCardPDF(school_name=school_name)
    pdf.add_page()
    
    # Student Details
    pdf.set_font('helvetica', '', 12)
    pdf.cell(0, 10, f"Student Name: {student.first_name} {student.last_name}")
    pdf.ln(8)
    pdf.cell(0, 10, f"Admission No: {student.admission_number}")
    pdf.ln(8)
    if student.parent:
        pdf.cell(0, 10, f"Parent: {student.parent.first_name} {student.parent.last_name}")
    pdf.ln(15)
    
    # Exam Results Table
    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(60, 10, "Subject", border=1)
    pdf.cell(40, 10, "Marks Obtained", border=1)
    pdf.cell(40, 10, "Max Marks", border=1)
    pdf.cell(40, 10, "Performance", border=1)
    pdf.ln()
    
    pdf.set_font('helvetica', '', 12)
    
    total_obtained = 0
    total_max = 0
    
    for result in exam_results:
        pdf.cell(60, 10, str(result.subject.name), border=1)
        pdf.cell(40, 10, str(result.marks_obtained), border=1)
        pdf.cell(40, 10, str(result.max_marks), border=1)
        
        # Calculate percentage for row
        try:
            percentage = (result.marks_obtained / result.max_marks) * 100
            grade = "Pass" if percentage >= 40 else "Fail"
        except:
            grade = "-"
            
        pdf.cell(40, 10, grade, border=1)
        pdf.ln()
        
        total_obtained += result.marks_obtained
        total_max += result.max_marks
        
    pdf.ln(10)
    
    # Summary
    if total_max > 0:
        final_percentage = (total_obtained / total_max) * 100
        pdf.set_font('helvetica', 'B', 14)
        pdf.cell(0, 10, f"Total Score: {total_obtained} / {total_max}", align='R')
        pdf.ln(8)
        pdf.cell(0, 10, f"Percentage: {final_percentage:.2f}%", align='R')
        
    # Output to buffer
    buffer = BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer
