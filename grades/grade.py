'''
Author:
Alexandros Kanterakis (kantale@ics.forth.gr)

This is a script to help grade exercises for this course
'''


import re
import os
import glob
import json
import email
import time
import argparse
import smtplib, ssl # For mail
import pandas as pd

from itertools import groupby
from collections import defaultdict
from os.path import expanduser

from get_ask import get_ask
from params import Params

try:
    from penalties import Penalties
except ImportError:
    class Penalties:
        PENALTIES: {}

class Utils:
    '''
    Useful generic utils
    '''
    @staticmethod
    def get_home_dir():
        '''
        '''
        return expanduser("~")

    @staticmethod
    def get_immediate_subdirectories(a_dir):
        '''
        https://stackoverflow.com/a/800201
        '''
        for name in os.listdir(a_dir):
            p = os.path.join(a_dir, name)
            
            if os.path.isdir(p):
                yield p 


class Mail:

    PASSWORD_PATH = '.gmail/settings.json'

    def __init__(self,):
        self.connect_to_gmail()

    @staticmethod
    def get_password():
        password_filename = os.path.join(
            Utils.get_home_dir(), 
            Mail.PASSWORD_PATH
        )

        with open(password_filename) as f:
            data = json.load(f)
        return data['password']

    def connect_to_gmail(self,):
        port = 587  # For starttls
        smtp_server = "smtp.gmail.com"
        sender_email = "alexandros.kanterakis@gmail.com"
        password = Mail.get_password() 

        context = ssl.create_default_context()
        self.server = smtplib.SMTP(smtp_server, port)

        self.server.ehlo()  # Can be omitted
        self.server.starttls(context=context)
        self.server.ehlo()  # Can be omitted
        self.server.login(sender_email, password)

        print ('CONNECTED TO GMAIL')



    def do_send_mail(self, to, subject, text, sleep=10, actually_send_mail=False):
        from email.header import Header
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        #msg = MIMEText(text, 'plain', 'utf-8') # If text is garbled, try this
        msg = MIMEText(text)

        sender_email = "alexandros.kanterakis@gmail.com"
        receiver_email = to


        email = MIMEMultipart('mixed') # email = MIMEMultipart()
        email['From'] = sender_email
        email['To'] = receiver_email
        email['Subject'] = Header(subject, 'utf-8')

        msg.set_payload(text.encode('utf-8')) #msg.set_payload(text.encode('ascii'))
        email.attach(msg)

        message = email.as_string()

        if False:
            message = 'Subject: {}\n\n{}'.format(subject, text)

        if actually_send_mail:
            self.server.sendmail(sender_email, receiver_email, message)
        else:
            print (text)
            #print (message)
        time.sleep(sleep)
        print ('Mail sent')

    def disconnect_from_gmail(self,):
        self.server.quit()
        print ('DISCONNECTED FROM GMAIL')



class Grades:

    # Filetypes
    IPYNB = 1
    MIME = 2
    PLAIN = 3

    declarations = [
        'askhsh','Askhsh','ASKHSH','Askisi','askisi',
        '΄askhsh','ΆΣΚΗΣΗ','ΑΣΚΗΣΗ','ασκηση','άσκηση',
        'Άσκηση','ασκιση', 'akshsh', 'Αskhsh', 'Askhsk', 
        'Απαντηση ασκησης', 'Απάντηση ασκησης', 'απαντηση ασκησης',
        'Task_', 'απαντηση ακσησης', 'απάντηση άσκησης',
        'this is the solution for ex.', r'-+ΑΣΚΗΣΗ',
        "'Ασκηση", "Αskisi", "Άσκση", "asksisi", 'Aslisi',
        'Ασκηση', "Task", "ask", "AKHSH", "aksisi", 'Akshsh',
        'askshsh', 'ασκ', '΄άσκηση', 'Asksh', 'Askhshh', 'asksi',
        'Ask', 'askkisi', 'aσκηση', 'ASkhsh', '΄Άσκηση', 'Akhsh',
        'Askhh', 'Askshsh', '΄΄Ασκηση', '΄΄Άσκηση', 'Άskisi', 'Αskisi',
        '.+skisi',

        'Exercise', 'exercise', 'ex', 'exercise.', 'Ex', 'Ex.',
        'excercise', 'exercice', 'EX', 'EX.'
    ]

    ex_regexp = re.compile(r'^\s*#+\s*({})\s*_*(?P<ask>\d+)'.format('|'.join(declarations)))

    SOLUTIONS_FILENAME_PATTERN = 'AM_{id_}_ASK_{ASK}'

    GRADE_RE = r'^-?\d+$' # The regexp that matched grades. 

    def __init__(self, directory, solutions_dir, action, 
            ex=None, 
            actually_send_mail=False,
            start = 1,
            end = 20,
            send_to_me=False,
            random_list=None,
            optional=None,
            show_answer_when_already_graded=False,
        ):
        self.dir = directory
        self.solutions_dir = solutions_dir
        self.actually_send_mail = actually_send_mail
        self.start = start
        self.end = end
        self.exercises_range = list(range(self.start, self.end+1))
        self.send_to_me = send_to_me
        self.all_anonymous_grades = [] # For plotting and statistics
        self.random_list = random_list
        self.optional = set(optional) if optional else set()
        self.show_answer_when_already_graded = show_answer_when_already_graded

        print (f'EXERCICE  DIR: {self.dir}')
        print (f'SOLUTIONS DIR: {self.solutions_dir}')

        self.get_filenames(ex)
        self.get_all_exercises()

        if action == 'grade':
            self.grade()
        elif action == 'send_mail':
            self.collect_all_grades()

            self.mail = Mail()
            self.send_mail()
            self.mail.disconnect_from_gmail()
        elif action == 'aggregate':
            pass # Do nothing
        else:
            raise Exception('Unknown action: {}'.format(action))

    def save_anonymoys_grades(self,):
        with open('grades.json', 'w') as f:
            json.dump(self.all_anonymous_grades, f)
        print ('Saved anonymous grades at: grades.json ')

    def get_solutions_filename(self, id_, exercise):

        filename = self.SOLUTIONS_FILENAME_PATTERN.format(id_=id_, ASK=exercise)

        return os.path.join(self.solutions_dir, filename)

    def get_grade_from_comment(self, comment=None, filename=None):

        if filename:
            with open(filename) as f:
                comment = f.read()

        grades = [
            int(x) 
            for x in comment.split('\n') 
                if re.match(self.GRADE_RE, x)
        ]

        assert len(grades) == 1
        assert grades[0] in list(range(0, 11)) + [-1] # -1 means: do not grade!
        if grades[0] == -1:
            return pd.NA

        return grades[0]

    def remove_grade_from_comment(self, comment):

        return '\n'.join(
            x 
            for x in comment.split('\n') 
                if not re.match(self.GRADE_RE, x)
        )

    def grade(self,):

        # How many answers are in total?
        total = len(self.all_exercises)
        print ('Total Answers:', total)

        for i, (exercise, id_, answer) in enumerate(self.all_exercises):

            filename = self.get_solutions_filename(id_, exercise)

            print ('Progress: {}/{} {:0.2f}%'.format(i+1, total, 100*(i+1)/total))
            print ('Exercise:', exercise)
            print ('      AM:', id_, '             Origin:', os.path.join(self.dir, id_))
            print ('Filename:', filename)
            print ('==================')

            #if id_ == '3052':
            #    print (answer)

            if os.path.exists(filename):
                print ('   Already graded..')
                if self.show_answer_when_already_graded:
                    print ('==ANSWER:==========')
                    print (answer)
                    print ('==COMMENTS:========')
                    with open(filename) as f:
                        comment = f.read()
                    print (comment)
                    print ('===================')

                continue

            print (answer)
            print ('==================')
            comment = ''
            while True:
                line = input() # NEVER USE INPUT!! 
                if line.strip() in ['q', 'Q', ';']:
                    break

                comment += line + '\n'

            # Is there a grade in there?
            grade = self.get_grade_from_comment(comment)

            # Good.. no exception happened. Save the comment
            with open(filename, 'w') as f:
                f.write(comment)

    def get_id_from_filename(self, filename):

        # Some files are like 1234.1 1234.2 ...
        dot_splitted = filename.split('.')
        if re.match(r'^\d+$', dot_splitted[-1]): # last part is a number
            filename = '.'.join(dot_splitted[:-1])

        return os.path.split(filename)[1]


    def get_all_exercises(self,):

        # Read all files
        data = []
        for filename in self.filenames:
            #print (filename)
            id_ = self.get_id_from_filename(filename)
            content = self.get_exercises(filename)

            try:
                for ask, solution in self.iterate_exercises(content, filename=filename):
                    data.append((id_, ask, solution))
            except Exception as e:
                print ('Problem in file:', filename)
                raise e

        # Group together multiple solutions to the same exercise from the same student
        self.all_exercises = defaultdict(dict)

        for group, it in groupby(sorted(data), lambda x : x[:2]):
            self.all_exercises[group[0]][group[1]] = '\n'.join(x[2] for x in it)

        # Print some stats..
        print ('Total students:', len(self.all_exercises))
        print ('Average exercises per student:', sum(len(v) for k,v in self.all_exercises.items())/len(self.all_exercises))

        # Some basic quality control..
        for k,v in self.all_exercises.items():
            for k2,v2 in v.items():
                assert k
                if not k2:
                    raise Exception('AM: {} Empty ASK:{} '.format(k, str(k2)))

        # Group and sort according to ask / AM
        self.all_exercises = sorted((int(k2), k, v2) for k,v in self.all_exercises.items() for k2,v2 in v.items())

    def collect_all_grades(self,):
        all_answers = {}

        #print (json.dumps(self.all_exercises, indent=4))
        #print ('=====')

        for ask, AM, answer in self.all_exercises:
            if not AM in all_answers:
                all_answers[AM] = {}

            assert not ask in all_answers[AM]

            filename = self.get_solutions_filename(AM, ask)
            with open(filename) as f:
                comment = f.read()

            grade = self.get_grade_from_comment(comment)
            comment = self.remove_grade_from_comment(comment)
            
            all_answers[AM][ask] = {
                'answer': answer,
                'grade': grade,
                'comment': comment,
            }
        self.all_answers = all_answers
        #print (json.dumps(self.all_answers, indent=4))

        self.all_anonymous_grades = [
            [
                v.get(i, {'grade':0})['grade'] for i in self.exercises_range
            ] 
            for k,v in all_answers.items()
        ]

        with open('grades.json', 'w') as f:
            # Remove NAN 
            to_save = [
                list(filter(pd.notna, x)) 
                for x in self.all_anonymous_grades
            ]
            json.dump(to_save, f)
        print ('Created anonymous grades.json')

    @staticmethod
    def create_mail_address(AM):
        if '@' in AM:
            return AM

        return 'bio' + AM + '@edu.biology.uoc.gr'

    @staticmethod
    def create_AM_from_email(email):
        m = re.fullmatch(r'bio(\d+)@edu\.biology\.uoc\.gr', email)
        if m:
            return m.group(1)

        return email

    def send_mail(self,):

        total = len(self.all_answers)
        for i, AM in enumerate(self.all_answers):

            if self.send_to_me:
                mail_address = 'alexandros.kanterakis@gmail.com'
            else:
                mail_address = Grades.create_mail_address(AM)
            
            print ('{}/{} -- {}'.format((i+1), total, mail_address)) # Don't comment this!

            mail = self.create_mail(AM)
            #print(mail) # Comment this! 

            if True:
                self.mail.do_send_mail(
                    to=mail_address, 
                    subject=Params.MAIL_SUBJECT.format(START=self.start, END=self.end), 
                    #subject=self.MAIL_SUBJECT_2,  # Final
                    text=mail,
                    actually_send_mail=self.actually_send_mail,
                )
            #a=1/0

    def create_exercise_mail(self, exercise, solution, comment, grade):

        if pd.isna(grade):
            grade_str = '---'
        else:
            grade_str = f'{grade}/10'

        return Params.MAIL_EXERCISE_PATTERN.format(
            EXERCISE = exercise,
            SOLUTION = solution,
            COMMENT = comment,
            GRADE = grade_str,
        )

    def create_mail(self, AM):

        exercises_mail = ''

        pandas_df = []

        if not self.random_list is None:
            required_list = get_ask(AM)
        else:
            required_list = None

        #for ASK, details in self.all_answers[AM].items():
        for ASK in self.exercises_range:

            if required_list and not ASK in required_list:
                continue

            if ASK in self.all_answers[AM]:
                details = self.all_answers[AM][ASK]

                answer = details['answer']
                comment = details['comment']
                grade = details['grade']
            else:
                answer = '\n'
                if ASK in self.optional:
                    comment = 'Αυτή η άσκηση είναι προαιρετική. Δεν θα μετρήσει στη βαθμολογία'
                    grade = pd.NA
                else:
                    comment =  Params.SUBMIT_NOTHING # 'Δεν έστειλες τίποτα για αυτή την άσκηση!'
                    grade = 0

            grade_dics = {Params.EXERCISE: ASK, Params.GRADE: grade} #{'Άσκηση': ASK, 'Βαθμός': grade}
            exercises_mail += self.create_exercise_mail(ASK, answer, comment, grade)
            pandas_df.append(grade_dics)

        pandas_df = pd.DataFrame(pandas_df)
        summary = pandas_df.to_string(index=False, na_rep='---')
        summary = summary.replace('<NA>', '  ---') # The above does not work!!!
        average = pandas_df[Params.GRADE].mean(skipna=True)
        summary += f'\n\n{Params.AVERAGE}: {average}'

        greeting = Params.GREETING.format(START=self.start, END=self.end) # Interim 
        #greeting = self.GREETING_2 # Final

        ret = Params.MAIL_PATTERN.format(
            GREETING=greeting,
            AM=AM,
            EXERCISES=exercises_mail,
            SUMMARY=summary,
        )

        return ret

    def get_type(self, filename):
        '''
        Return the type of file
        '''
        
        with open(filename) as f:
            content = f.read()

        # try to parse it as json
        try:
            data = json.loads(content)
        except json.decoder.JSONDecodeError:
            # This is not a JSON file..
            pass 
        else:
            # this is json.. assume ipynb..
            return self.IPYNB

        # Check if MIME. Any better way?
        if 'X-Google-Smtp-Source' in content:
            return self.MIME

        # Assuming file with content
        return self.PLAIN


    def iterate_exercises(self, text, filename=None):

        content = ''
        exercise = None
        for line in text.split('\n'):
            #print (line)
            m = re.match(self.ex_regexp, line)

            # Set this true to check declarations!
            if False:
                if re.match(r'^\s*#', line):
                    print (line, '-->', {True: 'MATCHED', False: 'NO MATCH!'}[bool(m)])
            if m:
                if exercise:
                    yield (exercise, content)
                    content = ''
                exercise = m.groupdict()['ask']

            content += '\n' + line

        if exercise is None:
            print (f'Could not find any exercise in file: {filename}')
            print (text)
            assert False

        yield (exercise, content)

    def get_exercises(self, filename):
        t = self.get_type(filename)
        
        if t == self.IPYNB:
            content = self.get_exercises_ipynb(filename)
        elif t == self.MIME:
            content = self.get_exercises_MIME(filename)
        elif t == self.PLAIN:
            content  = self.get_exercises_plain(filename)
        else:
            raise Exception('Unknown type={}'.format(t))

        return content


    def get_exercises_plain(self, filename):
        with open(filename) as f:
            content = f.read()

        return content

    def get_exercises_ipynb(self, filename):
        with open(filename) as f:
            content = json.load(f)

        code_cells = [
            ''.join(x['source']) for x in content['cells'] 
                if x['cell_type'] == 'code'
        ]
        return '\n\n'.join(code_cells)

    def get_exercises_MIME(self, filename):
        with open(filename) as f:
            content = f.read()

        m = email.message_from_string(content)
        payload = m.get_payload()
        #assert len(payload) == 21 # FIXME

        content = ""
        #for x in payload[1:]:
        for x in payload[:]:
            if hasattr(x, "get_payload"):
                content += '\n' + x.get_payload(decode=True).decode("utf-8")

        return content 

        
    def get_filenames(self, ex=None):
        if not ex:
            ex='*'
        else:
            ex = ex + '*'

        self.filenames = glob.glob(os.path.join(self.dir, ex))
        print ('Read: {} files'.format(len(self.filenames)))

    @staticmethod
    def get_project_grades(projects_dir = 'projects'):
        '''
        Get all projects
        '''

        gen = Utils.get_immediate_subdirectories(projects_dir)

        def normalize_AM(AM):
            if AM.startswith('bio'):
                assert re.fullmatch(r'bio\d+', AM)
                return AM.replace('bio', '')

            return AM

        ret = []

        for d in gen:

            project_path = os.path.split(d)[1]
            AMs = project_path.split('_')
            AMs = list(map(normalize_AM, AMs))

            #print (project_path, '-->', AMs)

            notes_filename = os.path.join(d, 'notes.md')
            
            try:
                with open(notes_filename) as f:
                    notes = f.read()
            except FileNotFoundError as e:
                print (f'WARNING: COULD NOT FIND: {notes_filename}')
                continue

            regexp = fr'\*\*{Params.GRADE}: ([\d\.]+)\*\*'
            m = re.search(regexp, notes)
            assert m, f'Regular expression {regexp} was not matched in file: {notes_filename}' 

            grade = float(m.group(1))
            assert 0<=grade<=10.0

            ret.append({
                'AMs': AMs,
                'grade': grade,
            })

        return ret




class Aggregator:
    '''
    Aggregates all grades
    '''

    
    TOTAL_FINAL = 10


    def __init__(self, 
        excel_filename = None, 
        optional=None,
        ex = None,
        send_to_me = False,
        actually_send_mail = False,
    ):

        self.excel_filename = excel_filename
        self.optional = set(map(int, optional)) if optional else set()
        self.ex = ex
        self.send_to_me = send_to_me
        self.actually_send_mail = actually_send_mail

        self.get_all_dirs()
        self.get_all_grades()
        self.average_grades()
        self.generate_excel()

    @staticmethod
    def final_grade(decimal_grade):
        g2 = round(decimal_grade * 10) / 10
        
        if g2 in [4.3, 4.4, 4.5, 4.6, 4.7]:
            return 5.0
        
        g3 = round(decimal_grade * 2) / 2
        
        return g3        

    def get_all_dirs(self,):

        self.all_exercise_dirs = glob.glob('exercises?')
        self.all_dirs = {
            'exercises': [],
            'final': {
                'exercises': 'final',
                'solutions': 'solutions_final',
            },
            'projects': 'projects',
        }

        for d in self.all_exercise_dirs:


            m = re.search(r'(\d+)$', d)
            assert m 
            n = int(m.group(1))
            dic = {
                'exercises': d,
                'solutions': f'solutions{n}',
            }
            self.all_dirs['exercises'].append(dic)

        print (f'All directories:')
        print (json.dumps(self.all_dirs, indent=4))

    def store_grades(self, grades, type_):
        '''
        type_ : `exercises` or 'final'
        '''
        for AM, grade in grades.all_answers.items():
            if not AM in self.all_grades:
                self.all_grades[AM] = {
                    'exercises': {},
                    'final': {},
                    'project': 0.0,
                }

            for exercise, exercise_d in grade.items():
                assert not exercise in self.all_grades[AM][type_]
                self.all_grades[AM][type_][exercise] = exercise_d['grade']

    def get_all_grades(self,):

        self.all_grades = {}

        # Get all exercise grades
        for exercise_round in self.all_dirs['exercises']:
            grades = Grades(
                directory = exercise_round['exercises'],
                solutions_dir = exercise_round['solutions'],
                action = 'aggregate', 
                ex = self.ex,
            )
            grades.collect_all_grades()
            self.store_grades(grades, type_='exercises')
            #print (grades.all_answers)  # {'1764': {1: {'answer': "\n# 'Ασκηση 1\n\ndef num(a):\n

        # If the final directory does not exist do not 
        # collect final grades
        if not os.path.exists(self.all_dirs['final']['exercises']):
            print ('Could not final exercise directory')
            self.has_final = False
        else:
            self.has_final = True
            print ('Collecting final grades')
            grades = Grades(
                directory = self.all_dirs['final']['exercises'],
                solutions_dir = self.all_dirs['final']['solutions'],
                action = 'aggregate',
                ex = self.ex,
            )
            grades.collect_all_grades()
            self.store_grades(grades, type_='final')   

        print ('Collecting project grades')
        project_grades = Grades.get_project_grades()
        for project_grade in project_grades:
            for AM in project_grade['AMs']:

                if self.ex:
                    if AM != self.ex:
                        continue

                assert AM in self.all_grades, f'Could not find {AM} in total grades'
                assert 'project' in self.all_grades[AM]
                self.all_grades[AM]['project'] = project_grade['grade']
        
    def average_grades(self,):

        self.lesson_grades = {}
        self.mail = Mail()

        final_grades = [] # Final grades for excel

        total = len(self.all_grades)
        c = 0
        for AM, grades in self.all_grades.items():
            c += 1

            text = Params.START_AGGREGATE_MAIL.format(AM=AM)

            exercises_sum = 0
            exercises_count = 0
            for x in range(1, Params.TOTAL_EXERCISES+1):
                text += f'{x}\t'

                if x in grades['exercises']:
                    g = grades['exercises'][x]

                    if pd.isna(g):
                        text += f'---\n'
                    elif x in self.optional and g == 0:
                        text += f'---\n'
                    else:
                        text += f'{g}\n'
                        exercises_sum += g
                        exercises_count += 1                        
                else:
                    if x in self.optional:
                        text += f'---\n'
                    else:
                        text += '0\n'
                        exercises_count += 1

            exercise_average = exercises_sum/exercises_count

            text += f'\n{Params.AVERAGE_EXERCISES}: {exercises_sum}/{exercises_count}={exercise_average}\n\n'


            if self.has_final:

                text += 'Τελικό Διαγώνισμα:\n'
                for k,v in grades['final'].items():
                    text += f'{k}\t{v}\n'

                nominator = sum(grades['final'].values())
                denominator = self.TOTAL_FINAL
                final_average = nominator/denominator

                text += f'Μέσος όρος τελικού: {nominator}/{denominator}={final_average}\n\n'
            else:
                final_average = 0.0

            project_average = grades['project']
            text += f'{Params.PROJECT_GRADE}: {project_average}\n\n'

            decimal_grade = Params.WEIGHT_FUN(
                exercises = exercise_average, 
                final=final_average, 
                project=project_average,
            )
            text += f'{Params.FINAL_FLOAT_GRADE}:\n'
            text += Params.FINAL_GRADE_FUN(
                exercise_average = exercise_average,
                final_average = final_average,
                project_average = project_average,
                decimal_grade = decimal_grade,
            ) 

            rounded_grade = Aggregator.final_grade(decimal_grade)
            text += f'{Params.FINAL_ROUNDED_GRADE}: {rounded_grade}\n\n'

            if AM in Penalties.PENALTIES:
                rounded_grade = Penalties.PENALTIES[AM]
                text += f'\n\nGrade After disciplinary actions: {rounded_grade}\n\n'

            text += Params.END_AGGREGATE_MAIL

            final_grades.append({'Email': AM, 'Final_Grade': rounded_grade})

            print (
                f'AM:{AM},'
                f' dec_grade: {decimal_grade},'
                f' rnd_grade: {rounded_grade},'
                f' ex: {exercise_average},'
                f' fin: {final_average},'
                f' proj: {project_average} '
            )
            #print (text)

            self.lesson_grades[AM] = rounded_grade

            if self.send_to_me:
                mail_address = 'alexandros.kanterakis@gmail.com'
            else:
                mail_address = Grades.create_mail_address(AM)
            subject = Params.FINAL_SUBJECT #'ΒΙΟΛ-494, Τελικός βαθμός'

            if self.actually_send_mail:
                self.mail.do_send_mail(
                        to=mail_address, 
                        subject=subject, 
                        text=text,
                        actually_send_mail=True,
                    )
                print (f'{c}/{total} Sent mail to: {mail_address}')
            else:
                print (text)

        self.mail.disconnect_from_gmail()

        # Create findal_grades excel
        final_grades_df = pd.DataFrame(final_grades)
        final_grades_df.to_excel('final_grades.xlsx')
        print ('Created: final_grades.xlsx')


    def generate_excel(self,
        new_column = 'Βαθ Εξετ 2',
        #AM_column = 'ΑΜ', # <-- Attention! this is Greek letters!
        AM_column = 'email', 
        AM_column_is_email = True,
        ):
        if not self.excel_filename:
            print ('Excel filename not found!')
            return

        print (f'Reading: {self.excel_filename}')
        original_excel = pd.read_excel(self.excel_filename)
        records = original_excel.to_dict('records')

        new_records = []
        in_excel = set()
        for record in records:

            new_dict = dict(record)
            AM = str(record[AM_column]) # this might be an email

            if AM_column_is_email:
                AM = Grades.create_AM_from_email(AM)

            if AM in self.lesson_grades:
                new_dict[new_column] = str(self.lesson_grades[AM])
            else:
                new_dict[new_column] = ''

            new_records.append(new_dict)
            in_excel.add(AM)

        # Get students with grades that are NOT in excel!
        students_with_grades = set(self.lesson_grades)

        students_with_grades_not_in_excel = students_with_grades-in_excel
        if students_with_grades_not_in_excel:
            print ('WARNING!!!!')
            print ('The following graded students are not in Excel!!!')
            for student in students_with_grades_not_in_excel:
                print (f'AM: {student}  Grade: {self.lesson_grades[student]}')
            print ('==================================================')

        new_excel = pd.DataFrame(new_records)
        new_excel.to_excel('grades.xlsx')
        print ('Generated: grades.xlsx')


if __name__ == '__main__':
    '''
    #GRADE
    python grade.py --dir /Users/admin/BME_17/exercises1 --sol /Users/admin/BME_17/solutions1 --action grade --start 1 --end 25 --show_answer_when_already_graded 
    
    #SEND EMAIL FOR EXERCISES
    python grade.py --dir /Users/admin/BME_17/exercises1 --sol /Users/admin/BME_17/solutions1  --action send_mail --start 1 --end 25
    python grade.py --dir /Users/admin/BME_17/exercises1 --sol /Users/admin/BME_17/solutions1  --action send_mail --start 1 --end 25 --ex alkaios.lmp@gmail.com --actually_send_mail --send_to_me 
    python grade.py --dir /Users/admin/BME_17/exercises1 --sol /Users/admin/BME_17/solutions1  --action send_mail --start 1 --end 25 --actually_send_mail  
    python grade.py --dir /Users/admin/BME_17/exercises1 --sol /Users/admin/BME_17/solutions1  --action send_mail --start 1 --end 25 --actually_send_mail --ex jacobgavalas.bme.uoc@gmail.com
    python grade.py --dir /Users/admin/BME_17/exercises1 --sol /Users/admin/BME_17/solutions1  --action send_mail --start 1 --end 25 --actually_send_mail --ex iropap94@gmail.com

    #AGGREGATE
    python grade.py --action aggregate --send_to_me --ex alkaios.lmp@gmail.com
    python grade.py --action aggregate --ex letsosalexandros@gmail.com 
    python grade.py --action aggregate --ex med12p1170012@med.uoc.gr
    python grade.py --action aggregate --ex manthostr@gmail.com 
    python grade.py --action aggregate  --ex manthostr@gmail.com  --actually_send_mail --send_to_me 
    python grade.py --action aggregate  --ex alkaios.lmp@gmail.com  --actually_send_mail --send_to_me 
    python grade.py --action aggregate  --actually_send_mail 

    ====================
    python grade.py --dir /Users/admin/biol-494/exercises/ --sol /Users/admin/biol-494/solutions --action grade
    python grade.py --dir /Users/admin/biol-494/exercises/ --sol /Users/admin/biol-494/solutions --action send_mail
    python grade.py --dir /Users/admin/biol-494/exercises/ --sol /Users/admin/biol-494/solutions --action send_mail --actually_send_mail
    python grade.py --dir /Users/admin/biol-494/exercises/ --ex 3158 --action grade 
    python grade.py --dir /Users/admin/biol-494/exercises/ --sol /Users/admin/biol-494/solutions --ex 2743 --action grade 
    python grade.py --dir /Users/admin/biol-494/exercises/ --sol /Users/admin/biol-494/solutions --ex 2743 --action send_mail --actually_send_mail

    # 2nd Round grade:
    python grade.py --dir /Users/admin/biol-494/exercises2/ --sol /Users/admin/biol-494/solutions2 --action grade --start 21 --end 40 

    # 2nd Round Send mail:
    python grade.py --dir /Users/admin/biol-494/exercises2/ --sol /Users/admin/biol-494/solutions2 --ex 2743 --action send_mail --start 21 --end 40  
    python grade.py --dir /Users/admin/biol-494/exercises2/ --sol /Users/admin/biol-494/solutions2 --ex 2743 --action send_mail --start 21 --end 40 --actually_send_mail  
    python grade.py --dir /Users/admin/biol-494/exercises2/ --sol /Users/admin/biol-494/solutions2 --ex 3052 --action send_mail --start 21 --end 40 --actually_send_mail --send_to_me
    python grade.py --dir /Users/admin/biol-494/exercises2/ --sol /Users/admin/biol-494/solutions2 --action send_mail --start 21 --end 40 --actually_send_mail  
    python grade.py --dir /Users/admin/biol-494/exercises2/ --sol /Users/admin/biol-494/solutions2 --ex 3052 --action send_mail --start 21 --end 40 --actually_send_mail


    python grade.py --dir /Users/admin/biol-494/exercises2/ --sol /Users/admin/biol-494/solutions2 --action send_mail --start 21 --end 40 --actually_send_mail 

    python grade.py --dir /Users/admin/biol-494/exercises/ --sol /Users/admin/biol-494/solutions --ex 2743 --action grade 

    python grade.py --dir /Users/admin/biol-494/exercises2/ --sol /Users/admin/biol-494/solutions2 --action grade

    # 3rd Round
    python grade.py --dir /Users/admin/biol-494/exercises3/ --sol /Users/admin/biol-494/solutions3 --action grade --start 41 --end 60 
    python grade.py --dir /Users/admin/biol-494/exercises3/ --sol /Users/admin/biol-494/solutions3 --ex 3053 --action send_mail --start 41 --end 60 --send_to_me --actually_send_mail   
    python grade.py --dir /Users/admin/biol-494/exercises3/ --sol /Users/admin/biol-494/solutions3  --action send_mail --start 41 --end 60 --actually_send_mail

    # 4th Round 
    python grade.py --dir /Users/admin/biol-494/exercises4/ --sol /Users/admin/biol-494/solutions4 --action grade --start 61 --end 80 
    python grade.py --dir /Users/admin/biol-494/exercises4/ --sol /Users/admin/biol-494/solutions4 --action send_mail --ex 3168 --send_to_me --actually_send_mail --start 61 --end 80 
    python grade.py --dir /Users/admin/biol-494/exercises4/ --sol /Users/admin/biol-494/solutions4 --action send_mail --ex 2729 --actually_send_mail --start 61 --end 80 
    python grade.py --dir /Users/admin/biol-494/exercises4/ --sol /Users/admin/biol-494/solutions4 --action send_mail --ex 2913 --actually_send_mail --start 61 --end 80 
    python grade.py --dir /Users/admin/biol-494/exercises4/ --sol /Users/admin/biol-494/solutions4 --action send_mail --ex 3125 --actually_send_mail --start 61 --end 80
    python grade.py --dir /Users/admin/biol-494/exercises4/ --sol /Users/admin/biol-494/solutions4 --action send_mail --ex 2898 --actually_send_mail --start 61 --end 80
    python grade.py --dir /Users/admin/biol-494/exercises4/ --sol /Users/admin/biol-494/solutions4 --action send_mail --ex 2871 --actually_send_mail --start 61 --end 80

    # 5th Round
    python grade.py --dir /Users/admin/biol-494/exercises5/ --sol /Users/admin/biol-494/solutions5 --action grade --start 81 --end 90  
    python grade.py --dir /Users/admin/biol-494/exercises5/ --sol /Users/admin/biol-494/solutions5 --ex 2970  --action send_mail --send_to_me --actually_send_mail --start 81 --end 90
    python grade.py --dir /Users/admin/biol-494/exercises5/ --sol /Users/admin/biol-494/solutions5 --action send_mail --actually_send_mail --start 81 --end 90  
    python grade.py --dir /Users/admin/biol-494/exercises5/ --sol /Users/admin/biol-494/solutions5 --ex 2967  --action send_mail --actually_send_mail --start 81 --end 90  
    python grade.py --dir /Users/admin/biol-494/exercises5/ --sol /Users/admin/biol-494/solutions5 --ex 3037  --action send_mail --actually_send_mail --start 81 --end 90  

    # 6th Round 
    python grade.py --dir /Users/admin/biol-494/exercises6/ --sol /Users/admin/biol-494/solutions6 --action grade --start 91 --end 100 --optional 94
    python grade.py --dir /Users/admin/biol-494/exercises6/ --sol /Users/admin/biol-494/solutions6 --action grade --start 91 --end 100 --ex 2979 
    python grade.py --dir /Users/admin/biol-494/exercises6/ --sol /Users/admin/biol-494/solutions6 --ex 2979  --action send_mail --start 91 --end 100  
    python grade.py --dir /Users/admin/biol-494/exercises6/ --sol /Users/admin/biol-494/solutions6 --ex 2979  --action send_mail --actually_send_mail  --start 91 --end 100
    python grade.py --dir /Users/admin/biol-494/exercises6/ --sol /Users/admin/biol-494/solutions6  --action send_mail  --start 91 --end 100 --optional 94 
    python grade.py --dir /Users/admin/biol-494/exercises6/ --sol /Users/admin/biol-494/solutions6  --action send_mail  --start 91 --end 100 --optional 94 --actually_send_mail  
    python grade.py --dir /Users/admin/biol-494/exercises6/ --sol /Users/admin/biol-494/solutions6 --ex 3103 --action send_mail  --start 91 --end 100 --optional 94 --actually_send_mail
    python grade.py --dir /Users/admin/biol-494/exercises6/ --sol /Users/admin/biol-494/solutions6 --ex 3089 --action send_mail  --start 91 --end 100 --optional 94 --actually_send_mail
    python grade.py --dir /Users/admin/biol-494/exercises6/ --sol /Users/admin/biol-494/solutions6 --ex 3052 --action send_mail  --start 91 --end 100 --optional 94 --actually_send_mail
    python grade.py --dir /Users/admin/biol-494/exercises6/ --sol /Users/admin/biol-494/solutions6 --ex 3094 --action send_mail  --start 91 --end 100 --optional 94 --actually_send_mail
    python grade.py --dir /Users/admin/biol-494/exercises6/ --sol /Users/admin/biol-494/solutions6 --ex 2871 --action send_mail  --start 91 --end 100 --optional 94 --actually_send_mail

    # final
    python grade.py --dir /Users/admin/biol-494/final/ --sol /Users/admin/biol-494/solutions_final --action grade --start 1 --end 100  
    python grade.py --dir /Users/admin/biol-494/final/ --sol /Users/admin/biol-494/solutions_final --action grade --start 1 --end 100 --ex 2979
    python grade.py --dir /Users/admin/biol-494/final/ --sol /Users/admin/biol-494/solutions_final --ex 2979  --action send_mail --random_list 10 --actually_send_mail --send_to_me --start 1 --end 100 
    python grade.py --dir /Users/admin/biol-494/final/ --sol /Users/admin/biol-494/solutions_final --ex 2979  --action send_mail --random_list 10 --actually_send_mail --start 1 --end 100 
    python grade.py --dir /Users/admin/biol-494/final/ --sol /Users/admin/biol-494/solutions_final --ex 3117  --action send_mail --random_list 10 --actually_send_mail --start 1 --end 100 --send_to_me
    python grade.py --dir /Users/admin/biol-494/final/ --sol /Users/admin/biol-494/solutions_final   --action send_mail --random_list 10 --actually_send_mail --start 1 --end 100 

    # Aggregate
    python grade.py --action aggregate 
    python grade.py --action aggregate --excel 494_ΒΙΟΛ-494.xlsx
    python grade.py --action aggregate --excel 494_ΒΙΟΛ-494.xlsx --optional 94
    python grade.py --action aggregate --excel 494_ΒΙΟΛ-494.xlsx --optional 94 --ex 2871 --send_to_me
    python grade.py --action aggregate --excel ΒΙΟΛ-494_Ιούνιος_2021.xlsx --optional 94 

    # BME-109 FINAL SEPTEMBER
    python grade.py --action grade --dir /Users/admin/biol-109/september/ --sol /Users/admin/biol-109/september_sol/  
    '''


    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", help="Directory with exercises")
    parser.add_argument("--sol", help="Directory with solutions")
    parser.add_argument("--ex", help="Examine only given ΑΜ")
    parser.add_argument("--action", help="What to do: grade")
    parser.add_argument("--actually_send_mail", action="store_true")
    parser.add_argument("--send_to_me", action="store_true")
    parser.add_argument("--show_answer_when_already_graded", action="store_true")
    parser.add_argument("--start", type=int, help="Start from")
    parser.add_argument("--end", type=int, help="Start end")
    parser.add_argument("--random_list", type=int, help='Number of random exercises')
    parser.add_argument("--optional", nargs='*', type=int, help="Optional exercises")
    parser.add_argument("--excel", help="Excel file with all students")
    args = parser.parse_args()

    if args.action == 'aggregate':
        a = Aggregator(
            excel_filename = args.excel,
            optional = args.optional,
            ex=args.ex,
            send_to_me=args.send_to_me,
            actually_send_mail=args.actually_send_mail,
        )
    else:
        g = Grades(directory=args.dir, ex=args.ex, solutions_dir=args.sol, 
            action=args.action,
            actually_send_mail=args.actually_send_mail,
            send_to_me=args.send_to_me,
            start = args.start,
            end = args.end,
            random_list = args.random_list,
            optional = args.optional,
            show_answer_when_already_graded = args.show_answer_when_already_graded,
        )
    
