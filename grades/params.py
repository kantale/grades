
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

    GREETING_EXERCISES_SEMTEMBER_EN = '''
Hello,

These are your grades for the September examination period in the course:
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
    MAIL_SUBJECT_4 = 'BME-17 - Grades of September exams'
    MAIL_SUBJECT_SEPTEMBER_EN = '{LESSON_CODE} - Grades of September exams'

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

'''
    START_AGGREGATE_MAIL_GR = '''
Γεια σας, παρακάτω ακολουθεί η λεπτομερής βαθμολογία σας στο μάθημα:

{COURSE_TITLE}

ΑΜ: {AM}

'''


    END_AGGREGATE_MAIL_EN = '''
For questions please send email to kantale@ics.forth.gr

Regards,
Alexandros Kanterakis
''' #  # 'Χαιρετώ,\n' 'Αλέξανδρος Καντεράκης\n'

    END_AGGREGATE_MAIL_GR = '''
Γεια απορίες παρακαλώ στείλτε mail στο kantale@ics.forth.gr ή DM στο slack.

Χαιρετώ,
Αλέξανδρος Καντεράκης
'''

    EXERCISE_EN = 'Exercise' # Άσκηση 
    EXERCISE_GR = 'Άσκηση'
    EXERCISES_EN = 'Exercises'
    EXERCISES_GR = 'Ασκήσεις'

    GRADE_EN = 'Grade' # Βαθμός 
    GRADE_GR = 'Βαθμός'

    AVERAGE_EN = 'Average' # Μέσος όρος
    AVERAGE_GR = 'Μέσος όρος'

    WEIGHT_FUN_1 = lambda *, exercises, final, project : (
        (0.5 * exercises) + 
        (0.0 * final) + 
        (0.5 * project)
    )
    FINAL_GRADE_FUN_1 = lambda *, exercise_average, final_average, project_average, decimal_grade :  f'0.5*{exercise_average} + 0.5*{project_average} = {decimal_grade}\n\n'



    WEIGHT_FUN_2 = lambda *, exercises, final, project : (
        (0.33 * exercises) + 
        (0.34 * final) + 
        (0.33 * project)
    )
    FINAL_GRADE_FUN_2 = lambda *, exercise_average, final_average, project_average, decimal_grade :  f'0.33*{exercise_average} + 0.34*{final_average} + 0.33*{project_average} = {decimal_grade}\n\n'

    WEIGHT_FUN_3 = lambda *, exercises, final, project : (
        (0.0 * exercises) + 
        (1.0 * final) + 
        (0.0 * project)
    )
    FINAL_GRADE_FUN_3 = lambda *, exercise_average, final_average, project_average, decimal_grade :  f'1.0*{final_average} = {decimal_grade}\n\n'


    TOTAL_EXERCISES = 100 
    TOTAL_FINAL = 10 # Denominator of final exercises sum

    GET_AM_FOR_GET_ASK = lambda x : int(re.search(r'bio(\d+)@edu\.biology\.uoc\.gr', x).group(1))
    GET_ASK_EXTRA_PARAMS = {}
    #GET_ASK_EXTRA_PARAMS = {'num': 20}

    PENALTIES = {} # {'student_AM': 0.0}

    @classmethod
    def set_profile(cls, profile_name,):

        if profile_name in ['BME_17']:
            cls.GRADE = cls.GRADE_EN
            cls.AVERAGE_EXERCISES = cls.AVERAGE_EXERCISES_EN
            cls.FINAL_FLOAT_GRADE = cls.FINAL_FLOAT_GRADE_EN
            cls.FINAL_ROUNDED_GRADE = cls.FINAL_ROUNDED_GRADE_EN
            cls.PROJECT_GRADE = cls.PROJECT_GRADE_EN
            cls.START_AGGREGATE_MAIL = cls.START_AGGREGATE_MAIL_EN
            cls.END_AGGREGATE_MAIL = cls.END_AGGREGATE_MAIL_EN
            cls.FINAL_SUBJECT = cls.FINAL_SUBJECT_EN
            cls.EXERCISE = cls.EXERCISE_EN
            cls.EXERCISES = cls.EXERCISES_EN
            cls.MAIL_EXERCISE_PATTERN = cls.MAIL_EXERCISE_PATTERN_EN
            cls.SUBMIT_NOTHING = cls.SUBMIT_NOTHING_EN
            cls.AVERAGE = cls.AVERAGE_EN
            cls.GREETING = cls.GREETING_EXERCISES_SEMTEMBER_EN
            cls.MAIL_PATTERN = cls.MAIL_PATTERN_EXERCISES_EN
            cls.MAIL_SUBJECT = cls.MAIL_SUBJECT_SEPTEMBER_EN

        elif profile_name in ['BIOL_109', 'BIOL_494']:
            cls.GRADE = cls.GRADE_GR
            cls.AVERAGE_EXERCISES = cls.AVERAGE_EXERCISES_GR
            cls.FINAL_FLOAT_GRADE = cls.FINAL_FLOAT_GRADE_GR
            cls.FINAL_ROUNDED_GRADE = cls.FINAL_ROUNDED_GRADE_GR
            cls.PROJECT_GRADE = cls.PROJECT_GRADE_GR
            cls.START_AGGREGATE_MAIL = cls.START_AGGREGATE_MAIL_GR
            cls.END_AGGREGATE_MAIL = cls.END_AGGREGATE_MAIL_GR
            cls.FINAL_SUBJECT = cls.FINAL_SUBJECT_GR
            cls.EXERCISE = cls.EXERCISE_GR
            cls.EXERCISES = cls.EXERCISES_GR
            cls.MAIL_EXERCISE_PATTERN = cls.MAIL_EXERCISE_PATTERN_GR
            cls.SUBMIT_NOTHING = cls.SUBMIT_NOTHING_GR
            cls.AVERAGE = cls.AVERAGE_GR
            cls.MAIL_PATTERN = MAIL_PATTERN_EXERCISES_GR


        if profile_name == 'BME_17':

            cls.LESSON_CODE = 'BME-17'
            cls.COURSE_TITLE = 'BME-17, Bio-Informatics' 


            cls.TOTAL_EXERCISES = 25
            cls.WEIGHT_FUN = cls.WEIGHT_FUN_1


            cls.all_dirs = {
                'exercises': [
                    {
                    'exercises': '/Users/admin/BME_17/exercises1/', 
                    'solutions': '/Users/admin/BME_17/solutions1/',
                    },
#                   {
#                    'exercises': '/Users/admin/BME_17/september', 
#                    'solutions': '/Users/admin/BME_17/september_solutions/',
#                    },

                ],

                'final': {
                    'exercises': 'final',
                    'solutions': 'solutions_final',
                },
                'projects': '/Users/admin/BME_17/projects/',
            }
            with open('/Users/admin/BME_17/penalties.json') as f:
                cls.PENALTIES = json.load(f)

        elif profile_name == 'BIOL_109':
            from get_ask_biol_109_september import get_ask
            cls.get_ask = get_ask

            cls.LESSON_CODE = 'ΒΙΟΛ-109'
            cls.COURSE_TITLE = 'ΒΙΟΛ-109 Χρήσεις του Η/Υ και Βιολογικές Βάσεις Δεδομένων'

            cls.WEIGHT_FUN = cls.WEIGHT_FUN_3
            cls.FINAL_GRADE_FUN = cls.FINAL_GRADE_FUN_3
            cls.TOTAL_EXERCISES = 0 # No exercises 

            cls.all_dirs = {
                'final': {
                    'exercises' : '/Users/admin/biol-109/september',
                    'solutions' : '/Users/admin/biol-109/september_sol',
                }
            }

        elif profile_name == 'BIOL_494':
            from get_ask_biol_494_september import get_ask
            cls.get_ask = get_ask

            cls.LESSON_CODE = 'ΒΙΟΛ-494'
            cls.COURSE_TITLE = 'ΒΙΟΛ-494 Εισαγωγή στον προγραμματισμό'

            # Options for September 
            cls.GET_ASK_EXTRA_PARAMS = {'num': 20}
            cls.TOTAL_EXERCISES = 0 
            cls.WEIGHT_FUN = cls.WEIGHT_FUN_3
            cls.FINAL_GRADE_FUN = cls.FINAL_GRADE_FUN_3
            cls.TOTAL_FINAL = 20


            cls.all_dirs = {
                'exercises_2': [
                    {
                        'exercises': '/Users/admin/biol-494/exercises1/',
                        'solutions': '/Users/admin/biol-494/solutions1/',
                    },
                    {
                        'exercises': '/Users/admin/biol-494/exercises2/',
                        'solutions': '/Users/admin/biol-494/solutions2/',
                    },
                    {
                        'exercises': '/Users/admin/biol-494/exercises3/',
                        'solutions': '/Users/admin/biol-494/solutions3/',
                    },
                    {
                        'exercises': '/Users/admin/biol-494/exercises4/',
                        'solutions': '/Users/admin/biol-494/solutions4/',
                    },
                    {
                        'exercises': '/Users/admin/biol-494/exercises5/',
                        'solutions': '/Users/admin/biol-494/solutions5/',
                    },
                    {
                        'exercises': '/Users/admin/biol-494/exercises6/',
                        'solutions': '/Users/admin/biol-494/solutions6/',
                    },

                ],
                'final': {
                    'exercises': '/Users/admin/biol-494/final_september/',
                    'solutions': '/Users/admin/biol-494/solutions_september/',
                }
            }

        else:
            raise Exception(f'Unknown Profile: {profile_name}')



if __name__ == '__main__':
    Params.set_profile('BME_17')

    print (Params.GREETING)

