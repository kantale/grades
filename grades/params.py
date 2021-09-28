
import re

class Params:

    GREETING_1 = '''
Hello,

These are your grades for the exercises {START}-{END} in the course: 
'''

    GREETING = '''
Γεια σας,

Παρακάτω ακολουθούν οι βαθμοί σας στην εξέταση Σεπτεμβρίου στο μάθημα:
'''

    MAIL_PATTERN_1 = '''
{GREETING}

BME-17  Bio-Informatics

Mail: {AM}


{EXERCISES}

================================
Summary:

{SUMMARY}

For questions please send email to: kantale@ics.forth.gr

Regards,
Alexandros Kanterakis
'''

    MAIL_PATTERN = '''
{GREETING}

ΒΙΟΛ-109 Χρήσεις του Η/Υ και Βιολογικές Βάσεις Δεδομένων

Mail/ΑΜ: {AM}


{EXERCISES}

================================
Περιληπτικά:

{SUMMARY}

Για απορίες παρακαλώ στείλτε μέιλ στο: kantale@ics.forth.gr ή με DM στο slack.

Χαιρετώ,
Αλέξανδρος Καντεράκης

'''

    MAIL_EXERCISE_PATTERN_1 = '''
================================
  Exercise: {EXERCISE}
================================
  You submitted:
--------------------------------
{SOLUTION}
--------------------------------
Comments:
{COMMENT}
--------------------------------
Grade: {GRADE}
--------------------------------
'''

    MAIL_EXERCISE_PATTERN = '''
================================
  Άσκηση: {EXERCISE}
================================
  Τι έστειλες:
--------------------------------
{SOLUTION}
--------------------------------
Σχόλια:
{COMMENT}
--------------------------------
Βαθμός: {GRADE}
--------------------------------
'''


    MAIL_SUBJECT_1 = 'BME-17 - Grades for exercises {START}-{END}'
    MAIL_SUBJECT = 'ΒΙΟΛ-109 - Βαθμός εξεταστικής Σεπτέμβριος 2021'

    SUBMIT_NOTHING_1 = 'You did not submit anything for this exercise'
    SUBMIT_NOTHING = 'Δεν έστειλες κάτι για αυτή την άσκηση'

    AVERAGE_EXERCISES_1 = 'Average exercises grade' #  'Μέσος όρος ασκήσεων'
    AVERAGE_EXERCISES = 'Μέσος όρος ασκήσεων' 


    PROJECT_GRADE_1 = "Project's Grade" # 
    PROJECT_GRADE = "Βαθμός Project"


    FINAL_FLOAT_GRADE_1 = 'Final float grade' # 'Τελικός δεκαδικός βαθμός'
    FINAL_FLOAT_GRADE = 'Τελικός δεκαδικός βαθμός'

    FINAL_ROUNDED_GRADE_1 = 'Final rounded grade' # 'Τελικός στρογγυλοποιημένος βαθμός'
    FINAL_ROUNDED_GRADE = 'Τελικός στρογγυλοποιημένος βαθμός'


    FINAL_SUBJECT_1 = 'ΒΜΕ-17, Final Grade' # 'ΒΙΟΛ-494, Τελικός βαθμός'
    FINAL_SUBJECT = 'ΒΙΟΛ-494, Τελικός βαθμός'


    START_AGGREGATE_MAIL = '''
Hello, below is your detailed grade in the course:

BME-17 Bio-Informatics

Mail: {AM}

Exercises:
'''

    END_AGGREGATE_MAIL = '''
For questions please send email to kantale@ics.forth.gr

Regards,
Alexandros Kanterakis
''' #  # 'Χαιρετώ,\n' 'Αλέξανδρος Καντεράκης\n'

    EXERCISE = 'Exercise' # Άσκηση 
    GRADE = 'Grade' # Βαθμός 
    AVERAGE = 'Average' # Μέσος όρος

    WEIGHT_FUN = lambda *, exercises, final, project : (
        (0.5 * exercises) + 
        (0.0 * final) + 
        (0.5 * project)
    )


    WEIGHT_FUN_2 = lambda *, exercises, final, project : (
        (0.33 * exercises) + 
        (0.34 * final) + 
        (0.33 * project)
    )

    #FINAL_GRADE_FUN = lambda *, exercise_average, final_average, project_average, decimal_grade :  f'0.33*{exercise_average} + 0.34*{final_average} + 0.33*{project_average} = {decimal_grade}\n\n'
    FINAL_GRADE_FUN = lambda *, exercise_average, final_average, project_average, decimal_grade :  f'0.5*{exercise_average} + 0.5*{project_average} = {decimal_grade}\n\n'

    TOTAL_EXERCISES = 25
    #TOTAL_EXERCISES = 100 

    GET_AM_FOR_GET_ASK = lambda x : int(re.search(r'bio(\d+)@edu\.biology\.uoc\.gr', x).group(1))





