
import re
import json

class Params:

    GREETING_EXERCISES_EN = '''
Hello,

These are your grades for the exercises {START}-{END} in the course: 
'''

    GREETING_EXERCISES_SEMTEMBER_GR = '''
Γεια σας,

Παρακάτω ακολουθούν οι βαθμοί σας στην εξέταση Σεπτεμβρίου στο μάθημα:
'''

    MAIL_PATTERN_EXERCISES_EN = '''
{GREETING}

{COURSE_TITLE}

Mail: {AM}


{EXERCISES}

================================
Summary:

{SUMMARY}

For questions please send email to: kantale@ics.forth.gr

Regards,
Alexandros Kanterakis
'''


    MAIL_PATTERN_EXERCISES_GR = '''
{GREETING}

{COURSE_TITLE}

Mail/ΑΜ: {AM}


{EXERCISES}

================================
Περιληπτικά:

{SUMMARY}

Για απορίες παρακαλώ στείλτε μέιλ στο: kantale@ics.forth.gr ή με DM στο slack.

Χαιρετώ,
Αλέξανδρος Καντεράκης

'''

    MAIL_EXERCISE_PATTERN_EN = '''
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

    MAIL_EXERCISE_PATTERN_GR = '''
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
    MAIL_SUBJECT_2 = 'ΒΙΟΛ-109 - Βαθμός εξεταστικής Σεπτέμβριος 2021'
    MAIL_SUBJECT_3 = 'ΒΙΟΛ-494 - Βαθμός εξεταστικής Σεπτέμβριος 2021'

    SUBMIT_NOTHING_EN = 'You did not submit anything for this exercise'
    SUBMIT_NOTHING_GR = 'Δεν έστειλες κάτι για αυτή την άσκηση'

    AVERAGE_EXERCISES_EN = 'Average exercises grade' #  'Μέσος όρος ασκήσεων'
    AVERAGE_EXERCISES_GR = 'Μέσος όρος ασκήσεων' 

    PROJECT_GRADE_EN = "Project's Grade" # 
    PROJECT_GRADE_GR = "Βαθμός Project"

    FINAL_FLOAT_GRADE_EN = 'Final float grade' # 'Τελικός δεκαδικός βαθμός'
    FINAL_FLOAT_GRADE_GR = 'Τελικός δεκαδικός βαθμός'

    FINAL_ROUNDED_GRADE_EN = 'Final rounded grade' # 'Τελικός στρογγυλοποιημένος βαθμός'
    FINAL_ROUNDED_GRADE_GR = 'Τελικός στρογγυλοποιημένος βαθμός'


    FINAL_SUBJECT_EN = '{LESSON_CODE}, Final Grade' # 'ΒΙΟΛ-494, Τελικός βαθμός'
    FINAL_SUBJECT_GR = '{LESSON_CODE}, Τελικός βαθμός'


    START_AGGREGATE_MAIL_EN = '''
Hello, below is your detailed grade in the course:

{COURSE_TITLE}

Mail: {AM}

Exercises:
'''

    END_AGGREGATE_MAIL_EN = '''
For questions please send email to kantale@ics.forth.gr

Regards,
Alexandros Kanterakis
''' #  # 'Χαιρετώ,\n' 'Αλέξανδρος Καντεράκης\n'

    EXERCISE_EN = 'Exercise' # Άσκηση 
    EXERCISE_GR = 'Άσκηση'

    GRADE_EN = 'Grade' # Βαθμός 
    GRADE_GR = 'Βαθμός'

    AVERAGE_EN = 'Average' # Μέσος όρος
    AVERAGE_GR = 'Μέσος όρος'

    WEIGHT_FUN_1 = lambda *, exercises, final, project : (
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

    TOTAL_EXERCISES = 100 

    GET_AM_FOR_GET_ASK = lambda x : int(re.search(r'bio(\d+)@edu\.biology\.uoc\.gr', x).group(1))
    #GET_ASK_EXTRA_PARAMS = {}
    GET_ASK_EXTRA_PARAMS = {'num': 20}

    PENALTIES = {} # {'student_AM': 0.0}

    @classmethod
    def set_profile(cls, profile_name,):

        if profile_name == 'BME_17':

            cls.LESSON_CODE = 'BME-17'
            cls.COURSE_TITLE = 'BME-17, Bio-Informatics' 

            cls.GRADE = cls.GRADE_EN
            cls.AVERAGE_EXERCISES = cls.AVERAGE_EXERCISES_EN
            cls.FINAL_FLOAT_GRADE = cls.FINAL_FLOAT_GRADE_EN
            cls.FINAL_ROUNDED_GRADE = cls.FINAL_ROUNDED_GRADE_EN
            cls.PROJECT_GRADE = cls.PROJECT_GRADE_EN
            cls.START_AGGREGATE_MAIL = cls.START_AGGREGATE_MAIL_EN
            cls.END_AGGREGATE_MAIL = cls.END_AGGREGATE_MAIL_EN
            cls.FINAL_SUBJECT = cls.FINAL_SUBJECT_EN

            cls.TOTAL_EXERCISES = 25
            cls.WEIGHT_FUN = cls.WEIGHT_FUN_1


            cls.all_dirs = {
                'exercises': [
                    {
                    'exercises': '/Users/admin/BME_17/exercises1/', 
                    'solutions': '/Users/admin/BME_17/solutions1/',
                    },
                ],

                'final': {
                    'exercises': 'final',
                    'solutions': 'solutions_final',
                },
                'projects': '/Users/admin/BME_17/projects/',
            }
            with open('/Users/admin/BME_17/penalties.json') as f:
                cls.PENALTIES = json.load(f)

        elif profile_name == 'BIOL-109':
            cls.COURSE_TITLE = 'ΒΙΟΛ-109 Χρήσεις του Η/Υ και Βιολογικές Βάσεις Δεδομένων'
        elif profile_name == 'BIOL-494':
            cls.COURSE_TITLE = 'ΒΙΟΛ-494 Εισαγωγή στον προγραμματισμό'
        else:
            raise Exception(f'Unknown Profile: {profile_name}')



if __name__ == '__main__':
    Params.set_profile('BME_17')

    print (Params.GREETING)

