#!/bin/bash
TABLES=("academics_classroom" "academics_subject" "academics_timetable" "academics_exam" "academics_examresult" "academics_librarybook" "academics_transportroute" "academics_teacherassignment" "academics_schoolevent" "students_student" "students_parent" "students_studentdocument" "teachers_teacher" "teachers_attendance" "finance_feetype" "finance_feestructure" "finance_feepayment")

for table in "${TABLES[@]}"; do
    echo "Processing $table..."
    sudo -u postgres psql -d sunrise_db -c "ALTER TABLE $table ADD COLUMN IF NOT EXISTS school_id bigint;" 2>/dev/null
done
