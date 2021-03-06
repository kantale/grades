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

#from get_ask import get_ask
#from get_ask_biol_109_september import get_ask
#from get_ask_biol_494_september import get_ask


from params import Params


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

    @staticmethod
    def get_basename(path):
        '''
        'aa/cc/dd.ee' --> 'dd'
        '''
        last_path = os.path.split(path)[1]
        return os.path.splitext(last_path)[0]


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



    def do_send_mail(self, to, subject, text, sleep=10, actually_send_mail=False, send_to_filename=False):
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
            time.sleep(sleep)
        elif send_to_filename:
            with open(send_to_filename, 'a') as f:
                f.write(text + '\n')
        else:
            print (f'Subject: {subject}')
            print (text)
            #print (message)
        
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
        '??askhsh','????????????','????????????','????????????','????????????',
        '????????????:?', '????????????', 'akshsh', '??skhsh', 'Askhsk', 
        '???????????????? ??????????????', '???????????????? ??????????????', '???????????????? ??????????????',
        'Task_', '???????????????? ??????????????', '???????????????? ??????????????',
        'this is the solution for ex.', r'-+????????????',
        "'????????????", "??skisi", "??????????", "asksisi", 'Aslisi',
        '????????????', "Task", "ask", "AKHSH", "aksisi", 'Akshsh',
        'askshsh', '??????', '??????????????', 'Asksh', 'Askhshh', 'asksi',
        'Ask', 'askkisi', 'a??????????', 'ASkhsh', '??????????????', 'Akhsh',
        'Askhh', 'Askshsh', '????????????????', '????????????????', '??skisi', '??skisi',
        '.+skisi', 'ASK', 'A??????????', r'ask\.', 'ASKISI', 'AKSHSH',
        'Ashsh',

        'Exercise', 'exercise', 'ex', 'exercise.', 'Ex', 'Ex.',
        'excercise', 'exercice', 'EX', 'EX.',

        'Project', 'P', 'PROJECT', 'project',

        'Thema', 'THEMA', '????????', 'thema', '????????', '????????', '????????', '????????',
    ]

    ex_regexp = re.compile(r'^\s*#+\s*({})\s*_*(?P<ask>\d+)'.format('|'.join(declarations)))

    SOLUTIONS_FILENAME_PATTERN = 'AM_{id_}_ASK_{ASK}'

    GRADE_RE = r'^-?\d+$' # The regexp that matched grades. 

    def __init__(self, directory, solutions_dir, action, 
            ex=None, 
            project = False, # Is this a project?
            final = False, # Is this a final?
            actually_send_mail=False,
            start = 1,
            end = 20,
            send_to_me=False,
            send_to_file=False,
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
        self.send_to_file = send_to_file
        self.all_anonymous_grades = [] # For plotting and statistics
        self.random_list = random_list
        self.optional = set(optional) if optional else set()
        self.show_answer_when_already_graded = show_answer_when_already_graded
        self.this_is_project = project
        self.this_is_final = final

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

        assert len(grades) == 1, f'len(grades) -> {len(grades)}'
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

        return f'bio{AM}@edu.biology.uoc.gr'

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

                if self.this_is_project:
                    mail_subject = Params.MAIL_PROJECT_SUBJECT
                elif self.this_is_final:
                    mail_subject = Params.MAIL_FINAL_SUBJECT
                else:
                    mail_subject = Params.MAIL_SUBJECT

                self.mail.do_send_mail(
                    to=mail_address, 
                    subject=mail_subject.format(
                        START=self.start, 
                        END=self.end,
                        LESSON_CODE = Params.LESSON_CODE,
                    ), 
                    #subject=self.MAIL_SUBJECT_2,  # Final
                    text=mail,
                    actually_send_mail=self.actually_send_mail,
                    send_to_filename = 'mails.txt' if self.send_to_file else None,
                )
            #a=1/0

    def create_exercise_mail(self, exercise, solution, comment, grade):

        if pd.isna(grade):
            grade_str = '---'
        else:
            grade_str = f'{grade}/10'

        if self.this_is_project:
            mail_exercise_pattern_f = Params.MAIL_PROJECT_PATTERN
        else:
            mail_exercise_pattern_f = Params.MAIL_EXERCISE_PATTERN

        return mail_exercise_pattern_f.format(
            EXERCISE = exercise,
            SOLUTION = solution,
            COMMENT = comment,
            GRADE = grade_str,
        )

    def create_mail(self, AM):

        exercises_mail = ''

        pandas_df = []

        if not self.random_list is None:
            required_list = Params.get_ask(Params.GET_AM_FOR_GET_ASK(AM), **Params.GET_ASK_EXTRA_PARAMS)
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
                    comment = '???????? ?? ???????????? ?????????? ??????????????????????. ?????? ???? ???????????????? ?????? ????????????????????'
                    grade = pd.NA
                else:
                    comment =  Params.SUBMIT_NOTHING # '?????? ???????????????? ???????????? ?????? ???????? ?????? ????????????!'
                    grade = 0

            grade_dics = {Params.EXERCISE: ASK, Params.GRADE: grade} #{'????????????': ASK, '????????????': grade}
            exercises_mail += self.create_exercise_mail(ASK, answer, comment, grade)
            pandas_df.append(grade_dics)

        # Number of non_optional
        non_optional = sum(not ASK in self.optional for ASK in self.exercises_range)

        pandas_df = pd.DataFrame(pandas_df)
        summary = pandas_df.to_string(index=False, na_rep='---')
        summary = summary.replace('<NA>', '  ---') # The above does not work!!!
        
        # There are two types of optional:
        # 1. If you did it, you will be graded with it.  
        # 2. BONUS: You will always get a gigher grade, if you did it. 
        if False: # Type 1
            average = pandas_df[Params.GRADE].mean(skipna=True) 
        if True: # Type 2 (Bonus)
            the_sum = pandas_df[Params.GRADE].sum(skipna=True)
            average = the_sum / non_optional

        summary += f'\n\n{Params.AVERAGE}: {average}'

        if self.this_is_project:
            greeting_f = Params.GREETING_PROJECT
        elif self.this_is_final:
            greeting_f = Params.GREETING_FINAL
        else:
            greeting_f = Params.GREETING
        greeting = greeting_f.format(START=self.start, END=self.end) # Interim 
        #greeting = self.GREETING_2 # Final

        ret = Params.MAIL_PATTERN.format(
            GREETING=greeting,
            COURSE_TITLE=Params.COURSE_TITLE,
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


    def check_start_end(self, exercise):
        if self.start and int(exercise) < self.start:
            return False

        if self.end and int(exercise) > self.end:
            return False 

        return True

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

                    if self.check_start_end(exercise):
                        yield (exercise, content)
                    content = ''
                exercise = m.groupdict()['ask']

            content += '\n' + line

        if exercise is None:
            print (text)            
            assert False, f'Could not find any exercise in file: {filename}'

        if self.check_start_end(exercise):
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

        # Ignore filenames starting with _
        filenames = [x for x in self.filenames if Utils.get_basename(x)[0] != '_']
        if len(filenames) != self.filenames:
            print (f'Ignoring {len(self.filenames)-len(filenames)} files')
            self.filenames = filenames



    @staticmethod
    def get_project_grades(projects_dir):
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
        self.all_dirs = Params.all_dirs

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
        if 'exercises' in self.all_dirs:
            for exercise_round in self.all_dirs['exercises']:
                grades = Grades(
                    directory = exercise_round['exercises'],
                    solutions_dir = exercise_round['solutions'],
                    action = 'aggregate', 
                    ex = self.ex,
                )
                grades.collect_all_grades()
                self.store_grades(grades, type_='exercises')
                #print (grades.all_answers)  # {'1764': {1: {'answer': "\n# '???????????? 1\n\ndef num(a):\n
        else:
            print ('No exercises found')

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

        if 'projects' in self.all_dirs:
            print ('Collecting project grades')
            project_grades = Grades.get_project_grades(self.all_dirs['projects'], )
            for project_grade in project_grades:
                for AM in project_grade['AMs']:

                    if self.ex:
                        if AM != self.ex:
                            continue

                    assert AM in self.all_grades, f'Could not find {AM} in total grades'
                    assert 'project' in self.all_grades[AM]
                    self.all_grades[AM]['project'] = project_grade['grade']
        else:
            print ('No projects found')
        
    def average_grades(self,):

        self.lesson_grades = {}
        self.mail = Mail()

        final_grades = [] # Final grades for excel

        total = len(self.all_grades)
        c = 0
        for AM, grades in self.all_grades.items():
            c += 1

            text = Params.START_AGGREGATE_MAIL.format(
                AM=AM, 
                COURSE_TITLE=Params.COURSE_TITLE
            )

            exercises_sum = 0
            exercises_count = 0

            if Params.TOTAL_EXERCISES:
                text += f'{Params.EXERCISES}:\n'
                df_p = []
                for x in range(1, Params.TOTAL_EXERCISES+1):
                    #text += f'{x}\t\t'

                    if x in grades['exercises']:
                        g = grades['exercises'][x]

                        if pd.isna(g):
                            #text += f'---\n'
                            text_grade = f'---'
                        elif x in self.optional and g == 0:
                            #text += f'---\n'
                            text_grade = f'---'
                        else:
                            #text += f'{g}\n'
                            text_grade = f'{g}'
                            exercises_sum += g
                            exercises_count += 1                        
                    else:
                        if x in self.optional:
                            #text += f'---\n'
                            text_grade = f'---'
                        else:
                            #text += '0\n'
                            text_grade = '0'
                            exercises_count += 1

                    df_p.append({Params.EXERCISE: x, Params.GRADE:text_grade})
                df = pd.DataFrame(df_p)
                text += df.to_string(index=False) + '\n'
                text += f'\n{Params.AVERAGE_EXERCISES}: {exercises_sum}/{exercises_count}={exercise_average}\n\n'

            if exercises_count:
                exercise_average = exercises_sum/exercises_count
            else:
                exercise_average = 0.0

            


            if self.has_final:

                text += '???????????? ????????????????????:\n'
                for k,v in grades['final'].items():
                    text += f'{k}\t{v}\n'

                nominator = sum(grades['final'].values())
                denominator = Params.TOTAL_FINAL
                final_average = nominator/denominator

                text += f'?????????? ???????? ??????????????: {nominator}/{denominator}={final_average}\n\n'
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

            if AM in Params.PENALTIES:
                rounded_grade = Params.PENALTIES[AM]
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
            subject = Params.FINAL_SUBJECT.format(LESSON_CODE=Params.LESSON_CODE)

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
        new_column = '?????? ???????? 2',
        #AM_column = '????', # <-- Attention! this is Greek letters!
        AM_column = 'email', 
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

def create_arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", help="Name of parameters in profile")
    parser.add_argument("--dir", help="Directory with exercises")
    parser.add_argument("--sol", help="Directory with solutions")
    parser.add_argument("--ex", help="Examine only given ????")
    parser.add_argument("--project", action="store_true", help="This is a project")
    parser.add_argument("--final", action="store_true", help="This is a final")
    parser.add_argument("--action", help="What to do: grade")
    parser.add_argument("--actually_send_mail", action="store_true")
    parser.add_argument("--send_to_me", action="store_true")
    parser.add_argument("--send_to_file", action="store_true")
    parser.add_argument("--show_answer_when_already_graded", action="store_true")
    parser.add_argument("--start", type=int, help="Start from")
    parser.add_argument("--end", type=int, help="Start end")
    parser.add_argument("--random_list", type=int, help='Number of random exercises')
    parser.add_argument("--optional", nargs='*', type=int, help="Optional exercises")
    parser.add_argument("--excel", help="Excel file with all students")

    return parser


def aggregate_2():
    import shlex
    parser = create_arg_parser()

    arg_lines = [
        '--profile BIOL_494 --dir /Users/admin/biol-494/exercises_2022_1 --sol /Users/admin/biol-494/solutions_2022_1 --action send_mail  --start 1 --end 18 --send_to_file',
        '--profile BIOL_494 --dir /Users/admin/biol-494/exercises_2022_2 --sol /Users/admin/biol-494/solutions_2022_2 --action send_mail  --start 19 --end 36 --send_to_file',
        '--profile BIOL_494 --dir /Users/admin/biol-494/exercises_2022_3 --sol /Users/admin/biol-494/solutions_2022_3 --action send_mail --start 37 --end 54 --send_to_file',
        '--profile BIOL_494 --dir /Users/admin/biol-494/exercises_2022_4 --sol /Users/admin/biol-494/solutions_2022_4 --action send_mail --start 55 --end 70 --send_to_file',
        '--profile BIOL_494 --dir /Users/admin/biol-494/exercises_2022_5 --sol /Users/admin/biol-494/solutions_2022_5 --action send_mail --start 71 --end 90 --send_to_file',
        '--profile BIOL_494 --dir /Users/admin/biol-494/exercises_2022_6 --sol /Users/admin/biol-494/solutions_2022_6 --action send_mail --start 91 --end 100 --send_to_file',
        '--profile BIOL_494 --dir /Users/admin/biol-494/projects_2022 --sol /Users/admin/biol-494/projects_2022_solutions --action send_mail --start 1 --end 10  --project --send_to_file',
        '--profile BIOL_494 --dir /Users/admin/biol-494/final_2022 --sol /Users/admin/biol-494/solutions_final_2022 --action send_mail --start 1 --end 11 --optional 11  --final --send_to_file',


    ]


    for arg_line in arg_lines:

        args = parser.parse_args(shlex.split(arg_line))

        Params.set_profile(args.profile)
        g = Grades(
                directory=args.dir, 
                ex=args.ex, 
                project=args.project,
                final=args.final,
                solutions_dir=args.sol,
                action=args.action,
                actually_send_mail=args.actually_send_mail,
                send_to_me=args.send_to_me,
                send_to_file=args.send_to_file,
                start = args.start,
                end = args.end,
                random_list = args.random_list,
                optional = args.optional,
                show_answer_when_already_graded = args.show_answer_when_already_graded,
        )


    with open('mails.txt') as f:

        grades = {}

        for l in f:
            #print (l.strip())
            if re.search(r'???????????????? ???????????????????? ???? ???????????? ?????? ???????? ???????????????? 1-11 ?????? ?????????????? ?????????????????????????? ?????? ????????????', l):
                kind = 'final'
            if re.search(r'???????????????? ???????????????????? ???? ???????????? ?????? ???????? ???????????????? \d+-\d+ ?????? ????????????', l):
                kind = 'exercises'
            if re.search(r'???????????????? ???????????????????? ???? ???????????? ?????? ?????? projects 1-10 ?????? ????????????', l):
                kind = 'projects'

            s = re.search(r'Mail/????: ([\w\@\.]+)', l)
            if s:
                AM = s.group(1)

                assert kind
                if not AM in grades:
                    grades[AM] = {}

                if not kind in grades[AM]:
                    grades[AM][kind] = {}

            if re.search(r'??????????????????????:', l):
                for l2 in f:
                    s = re.search(r'\s+(\d+)\s+([\d-]+)', l2)
                    if s:
                        ask = int(s.group(1))
                        grade = s.group(2)
                        if ask in grades[AM][kind]:
                            print (f'Line: {l2}')
                            print (f'Ask: {ask} seen twice in dictionary')
                            assert False
                        grades[AM][kind][ask] = grade


                    s = re.search(r'?????????? ????????: [\d\.]+', l2)
                    if s:
                        kind = None
                        AM = None
                        break

        #print (grades)

    # Create mail
    text_f = '''
???????? ??????,
?? ?????????????? ?????? ???????????? ?????? ???????????? ????????-494, ???????????????? ???????? ????????????????????????????, ??????????: {final_grade}

???????????????? ?????????????????? ?????? ?????????????? ?????? ?????????????????? ?????? ????????????:


????: {AM}

????????????????:
=========
{exercises}

?????????? ???????? ????????????????: {exercises_average}

Projects:
=========
{projects}

?????????? ???????? project: {projects_average}

???????????? ??????????????:
===============
{final}

?????????? ???????? (????????????) ????????????????: {final_average}

???????????? ??????????????????:
=================
???? ???????????????????????????????????? ????????????:
(0.33*{exercises_average}) + (0.33*{projects_average}) + (0.34*{final_average}) = {final_grade_not_rounded}

???????????????????????????????????? ?????????????? ???????????? ??????????????????: {final_grade}

?????? ?????????????? ???????????????? ?????????????? ???????? ??????: kantale@ics.forth.gr ?? ???? DM ?????? slack.

??????????????,
???????????????????? ????????????????????
'''
    for AM, d in grades.items():

        for x in range(1,101):
            if not x in d['exercises']:
                d['exercises'][x] = 0
            else:
                 d['exercises'][x] = int(d['exercises'][x])


        exercises = sorted(d['exercises'].items(), key=lambda x: x[0])
        exercises = pd.DataFrame({
            '????????????': [x[0] for x in exercises],
            '????????????': [x[1] for x in exercises],
        })
        exercises_average = exercises['????????????'].mean()
        exercises = exercises.to_string(index=False, na_rep='---')

        if not 'projects' in d:
            d['projects'] = {}

        for x in range(1,11):
            if x in d['projects']:
                d['projects'][x] = int(d['projects'][x])
            else:
                d['projects'][x] = 0

        projects = sorted(d['projects'].items(), key=lambda x: x[0])
        projects = pd.DataFrame({
            'Project': [x[0] for x in projects],
            '????????????': [x[1] for x in projects],
        })
        projects_average = projects['????????????'].mean()
        projects = projects.to_string(index=False, na_rep='---')

        if not 'final' in d:
            d['final'] = {}

        for x in range(1,12):
            if x in d['final']:
                if d['final'][x] == '---':
                    d['final'][x] = 0
                else:
                    d['final'][x] = int(d['final'][x])
            else:
                d['final'][x] = 0

        final = sorted(d['final'].items(), key=lambda x: x[0])
        final = pd.DataFrame({
            '????????': [x[0] for x in final],
            '????????????': [x[1] for x in final],
        })
        final_average = final['????????????'].sum() / 10.0
        final = final.to_string(index=False, na_rep='---')
        final = re.sub(r'11(\s+)\s0', r'11\1---', final)

        final_grade_not_rounded = 0.33 * exercises_average + 0.33 * projects_average + 0.34 * final_average
        final_grade = Aggregator.final_grade(final_grade_not_rounded)

        text = text_f.format(
            AM=AM,
            exercises=exercises,
            exercises_average = exercises_average,
            projects=projects,
            projects_average=projects_average,
            final=final,
            final_average=final_average,
            final_grade_not_rounded=final_grade_not_rounded, 
            final_grade=final_grade,
        )

        print (text)
        #a=1/0

if __name__ == '__main__':
    '''
    p3 grade.py --profile BIOL_494 --dir /Users/admin/biol-494/exercises_2022_1 --sol /Users/admin/biol-494/solutions_2022_1 --action grade  --start 1 --end 18
    p3 grade.py --profile BIOL_494 --dir /Users/admin/biol-494/exercises_2022_1 --sol /Users/admin/biol-494/solutions_2022_1 --action send_mail  --start 1 --end 18 --ex 3235 --send_to_me --actually_send_mail
    p3 grade.py --profile BIOL_494 --dir /Users/admin/biol-494/exercises_2022_1 --sol /Users/admin/biol-494/solutions_2022_1 --action send_mail  --start 1 --end 18 --ex 3235 --actually_send_mail --ex 3051 

    p3 grade.py --profile BIOL_494 --dir /Users/admin/biol-494/exercises_2022_2 --sol /Users/admin/biol-494/solutions_2022_2 --action grade --start 19 --end 36 
    p3 grade.py --profile BIOL_494 --dir /Users/admin/biol-494/exercises_2022_2 --sol /Users/admin/biol-494/solutions_2022_2 --action send_mail  --start 19 --end 36 --ex 3235 --send_to_me --actually_send_mail
    p3 grade.py --profile BIOL_494 --dir /Users/admin/biol-494/exercises_2022_2 --sol /Users/admin/biol-494/solutions_2022_2 --action send_mail  --start 19 --end 36 --actually_send_mail


    p3 grade.py --profile BIOL_494 --dir /Users/admin/biol-494/exercises_2022_3 --sol /Users/admin/biol-494/solutions_2022_3 --action grade --start 37 --end 54
    p3 grade.py --profile BIOL_494 --dir /Users/admin/biol-494/exercises_2022_3 --sol /Users/admin/biol-494/solutions_2022_3 --action send_mail --start 37 --end 54  --ex 3235 --send_to_me --actually_send_mail
    p3 grade.py --profile BIOL_494 --dir /Users/admin/biol-494/exercises_2022_3 --sol /Users/admin/biol-494/solutions_2022_3 --action send_mail --start 37 --end 54 --actually_send_mail
    p3 grade.py --profile BIOL_494 --dir /Users/admin/biol-494/exercises_2022_3 --sol /Users/admin/biol-494/solutions_2022_3 --action send_mail --start 37 --end 54 --actually_send_mail --ex 3045 


    p3 grade.py --profile BIOL_494 --dir /Users/admin/biol-494/exercises_2022_4 --sol /Users/admin/biol-494/solutions_2022_4 --action grade --start 55 --end 70
    p3 grade.py --profile BIOL_494 --dir /Users/admin/biol-494/exercises_2022_4 --sol /Users/admin/biol-494/solutions_2022_4 --action send_mail --start 55 --end 70 --ex 3045 --send_to_me --actually_send_mail
    p3 grade.py --profile BIOL_494 --dir /Users/admin/biol-494/exercises_2022_4 --sol /Users/admin/biol-494/solutions_2022_4 --action send_mail --start 55 --end 70 --actually_send_mail 
    p3 grade.py --profile BIOL_494 --dir /Users/admin/biol-494/exercises_2022_4 --sol /Users/admin/biol-494/solutions_2022_4 --action send_mail --start 55 --end 70 --actually_send_mail --ex 3114 
    p3 grade.py --profile BIOL_494 --dir /Users/admin/biol-494/exercises_2022_4 --sol /Users/admin/biol-494/solutions_2022_4 --action send_mail --start 55 --end 70 --actually_send_mail --ex 3147 
    p3 grade.py --profile BIOL_494 --dir /Users/admin/biol-494/exercises_2022_4 --sol /Users/admin/biol-494/solutions_2022_4 --action send_mail --start 55 --end 70 --actually_send_mail --ex 3072

    p3 grade.py --profile BIOL_494 --dir /Users/admin/biol-494/exercises_2022_5 --sol /Users/admin/biol-494/solutions_2022_5 --action grade --start 71 --end 90
    p3 grade.py --profile BIOL_494 --dir /Users/admin/biol-494/exercises_2022_5 --sol /Users/admin/biol-494/solutions_2022_5 --action send_mail --start 71 --end 90 --ex 3235 --send_to_me --actually_send_mail
    p3 grade.py --profile BIOL_494 --dir /Users/admin/biol-494/exercises_2022_5 --sol /Users/admin/biol-494/solutions_2022_5 --action send_mail --start 71 --end 90 --actually_send_mail
    p3 grade.py --profile BIOL_494 --dir /Users/admin/biol-494/exercises_2022_5 --sol /Users/admin/biol-494/solutions_2022_5 --action send_mail --start 71 --end 90 --actually_send_mail --ex 3092 


    p3 grade.py --profile BIOL_494 --dir /Users/admin/biol-494/exercises_2022_6 --sol /Users/admin/biol-494/solutions_2022_6 --action grade --start 91 --end 100
    p3 grade.py --profile BIOL_494 --dir /Users/admin/biol-494/exercises_2022_6 --sol /Users/admin/biol-494/solutions_2022_6 --action send_mail --start 91 --end 100 --ex 3235 --send_to_me --actually_send_mail 
    p3 grade.py --profile BIOL_494 --dir /Users/admin/biol-494/exercises_2022_6 --sol /Users/admin/biol-494/solutions_2022_6 --action send_mail --start 91 --end 100 --ex 3115 
    p3 grade.py --profile BIOL_494 --dir /Users/admin/biol-494/exercises_2022_6 --sol /Users/admin/biol-494/solutions_2022_6 --action send_mail --start 91 --end 100 --actually_send_mail 
    p3 grade.py --profile BIOL_494 --dir /Users/admin/biol-494/exercises_2022_6 --sol /Users/admin/biol-494/solutions_2022_6 --action send_mail --start 91 --end 100 --actually_send_mail --ex 3115 
    p3 grade.py --profile BIOL_494 --dir /Users/admin/biol-494/exercises_2022_6 --sol /Users/admin/biol-494/solutions_2022_6 --action send_mail --start 91 --end 100 --actually_send_mail --ex 3148

    p3 grade.py --profile BIOL_494 --dir /Users/admin/biol-494/projects_2022 --sol /Users/admin/biol-494/projects_2022_solutions --action grade --start 1 --end 10 --ex 2936
    p3 grade.py --profile BIOL_494 --dir /Users/admin/biol-494/projects_2022 --sol /Users/admin/biol-494/projects_2022_solutions --action send_mail --start 1 --end 10 --ex 2936  --project 
    p3 grade.py --profile BIOL_494 --dir /Users/admin/biol-494/projects_2022 --sol /Users/admin/biol-494/projects_2022_solutions --action send_mail --start 1 --end 10 --ex 2936  --project --send_to_me --actually_send_mail  
    p3 grade.py --profile BIOL_494 --dir /Users/admin/biol-494/projects_2022 --sol /Users/admin/biol-494/projects_2022_solutions --action send_mail --start 1 --end 10 --ex 2936  --project --actually_send_mail
    p3 grade.py --profile BIOL_494 --dir /Users/admin/biol-494/projects_2022 --sol /Users/admin/biol-494/projects_2022_solutions --action grade --start 1 --end 10 
    p3 grade.py --profile BIOL_494 --dir /Users/admin/biol-494/projects_2022 --sol /Users/admin/biol-494/projects_2022_solutions --action send_mail --start 1 --end 10 --project --actually_send_mail
    p3 grade.py --profile BIOL_494 --dir /Users/admin/biol-494/projects_2022 --sol /Users/admin/biol-494/projects_2022_solutions --action send_mail --start 1 --end 10 --project --actually_send_mail --ex 3214 

    p3 grade.py --profile BIOL_494 --dir /Users/admin/biol-494/final_2022 --sol /Users/admin/biol-494/solutions_final_2022 --action grade --start 1 --end 11 --ex 2936
    p3 grade.py --profile BIOL_494 --dir /Users/admin/biol-494/final_2022 --sol /Users/admin/biol-494/solutions_final_2022 --action send_mail --start 1 --end 10 --ex 2936 --final
    p3 grade.py --profile BIOL_494 --dir /Users/admin/biol-494/final_2022 --sol /Users/admin/biol-494/solutions_final_2022 --action send_mail --start 1 --end 10 --ex 2936 --final --send_to_me --actually_send_mail  
    p3 grade.py --profile BIOL_494 --dir /Users/admin/biol-494/final_2022 --sol /Users/admin/biol-494/solutions_final_2022 --action send_mail --start 1 --end 10 --ex 2936 --final  --actually_send_mail  
    p3 grade.py --profile BIOL_494 --dir /Users/admin/biol-494/final_2022 --sol /Users/admin/biol-494/solutions_final_2022 --action grade --start 1 --end 11

    p3 grade.py --profile BIOL_494 --dir /Users/admin/biol-494/final_2022 --sol /Users/admin/biol-494/solutions_final_2022 --action send_mail --start 1 --end 11 --optional 11  --final
    p3 grade.py --profile BIOL_494 --dir /Users/admin/biol-494/final_2022 --sol /Users/admin/biol-494/solutions_final_2022 --action send_mail --start 1 --end 11 --optional 11  --final --ex 2936 --send_to_me --actually_send_mail  
    p3 grade.py --profile BIOL_494 --dir /Users/admin/biol-494/final_2022 --sol /Users/admin/biol-494/solutions_final_2022 --action send_mail --start 1 --end 11 --optional 11  --final --actually_send_mail  
    p3 grade.py --profile BIOL_494 --dir /Users/admin/biol-494/final_2022 --sol /Users/admin/biol-494/solutions_final_2022 --action send_mail --start 1 --end 11 --optional 11  --final --actually_send_mail  --ex 3127 
    '''

    if True:
        aggregate_2()
        a=1/0

    parser = create_arg_parser()
    args = parser.parse_args()

    Params.set_profile(args.profile)

    if args.action == 'aggregate':
        a = Aggregator(
            excel_filename = args.excel,
            optional = args.optional,
            ex=args.ex,
            send_to_me=args.send_to_me,
            actually_send_mail=args.actually_send_mail,
        )
    else:
        g = Grades(
            directory=args.dir, 
            ex=args.ex, 
            project=args.project,
            final=args.final,
            solutions_dir=args.sol,
            action=args.action,
            actually_send_mail=args.actually_send_mail,
            send_to_me=args.send_to_me,
            start = args.start,
            end = args.end,
            random_list = args.random_list,
            optional = args.optional,
            show_answer_when_already_graded = args.show_answer_when_already_graded,
        )
    

