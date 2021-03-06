import pymssql
import sys
from passlib.hash import pbkdf2_sha256


class SQL:
    def __init__(self, ):
        self.mydb = pymssql.connect(
            host=sys.argv[1],
            user=sys.argv[2],
            password=sys.argv[3],
            database=sys.argv[4]
        )
        self.mydb.autocommit(True)
        self.my_cursor = self.mydb.cursor()

    def get_all_course_students(self, how_many):
        self.my_cursor.execute('''Select CS.GradePercentage, info.GPA as StudentGPA,
        info.TotalCreditHours as StudentTotalCreditHours, info.OnCampus as StudentOnCampus,
        info.IsWorking as StudentIsWorking, coalesce(AST.HasPosition, 0) as StudentHasActivityPosition,
        C.CreditHours as CourseCreditHours, C.CourseLevel,
        case when CT.CourseTypeId = 1 then 1 else 0 end as AestheticInterpretation,
        case when CT.CourseTypeId = 2 then 1 else 0 end as EmpiricalandQuantitativeReasoning,
        case when CT.CourseTypeId = 3 then 1 else 0 end as EthicalReasoningandResponsibility,
        case when CT.CourseTypeId = 4 then 1 else 0 end as GlobalIssuesandPerspectives,
        case when CT.CourseTypeId = 5 then 1 else 0 end as HistoricalPerspectives,
        case when CT.CourseTypeId = 6 then 1 else 0 end as HumanDiversitywithintheUS,
        case when CT.CourseTypeId = 7 then 1 else 0 end as NaturalandPhysicalSciences,
        case when CT.CourseTypeId = 8 then 1 else 0 end as SocialSciences,
        I.YearsTeaching, I.IsTenured, I.Degree
        from (
            Select SUM(C.CreditHours) as TotalCreditHours, S.StudentId, S.GPA, S.OnCampus, S.IsWorking
            from CourseStudent CS
            join Course C on C.CourseId = CS.CourseId
            join Student S on S.StudentId = CS.StudentId
            group by S.StudentId, S.GPA, S.OnCampus, S.IsWorking
        ) as info
        left join ActivityStudent AST on AST.StudentId = info.StudentId 
        join CourseStudent CS on CS.StudentId = info.StudentId
        join Course C on C.CourseId = CS.CourseId
        join CourseType CT on CT.CourseTypeId = C.CourseTypeId
        join CourseInstructor CI on CI.CourseId = C.CourseId
        join Instructor I on I.InstructorId = CI.InstructorId;''')
        return self.my_cursor.fetchmany(how_many)

    def sign_in(self, email, raw):
        row = self.get_hashed(email)
        if row is None:
            return False
        else:
            return pbkdf2_sha256.verify(raw, row)

    def get_hashed(self, email):
        self.my_cursor.execute('''
            SELECT S.HashedPass
            From Student S
            Where S.Email = '{}'
        '''.format(email))
        row = self.my_cursor.fetchone()
        if row is None:
            return None
        return row[0]

    def get_home_info(self, email):
        self.my_cursor.execute('''
            SELECT CT.CourseTypeName, C.CourseLevel, C.CreditHours, CT.CourseTypeName, CS.GradePercentage
            FROM Student S
            Join CourseStudent CS on CS.StudentId = S.StudentId
            Join Course C on C.CourseId = CS.CourseId
            Join CourseType CT on C.CourseTypeId = CT.CourseTypeId
            Where S.Email = '{}'
            '''.format(email))
        return self.my_cursor.fetchall()

    def get_student_first_name(self, email):
        self.my_cursor.execute('''
            SELECT S.FirstName
            FROM Student S
            where S.Email = '{}'   
        '''.format(email))
        return self.my_cursor.fetchone()[0]

    def create_student(self, password, first_name, last_name, on_campus, is_working, gpa, email, institution_id):
        self.my_cursor.execute('''
            INSERT INTO Student(HashedPass, FirstName, LastName, OnCampus, IsWorking, GPA, Email, InstitutionId)
            VALUES ('{}' ,'{}', '{}', {}, {}, {}, '{}', {});
        '''.format(password, first_name, last_name, on_campus, is_working, gpa, email, institution_id))

    def get_student_info_by_email(self, email):
        self.my_cursor.execute('''
            Select S.FirstName,S.LastName, S.OnCampus, S.IsWorking, S.GPA
            FROM Student S
            Where S.Email = '{}';
        '''.format(email))
        return self.my_cursor.fetchone()

    def get_student_grades_by_course(self, course_id):
        self.my_cursor.execute('''
            SELECT CS.GradePoints
            FROM CourseStudent CS
            WHERE CS.CourseId = {}
        '''.format(course_id))
        return self.my_cursor.fetchone()

    def get_student_info_by_course_id(self, course_id):
        self.my_cursor.execute('''
                    SELECT *
                    FROM CourseStudent CS
                    JOIN Student S on S.StudentId = CS.StudentId
                    WHERE CS.CourseId = {}
                '''.format(course_id))
        return self.my_cursor.fetchall()

    def update_student_info(self, firstname, lastname, oncampus, isworking, gpa, email):
        self.my_cursor.execute('''
            UPDATE Student
            SET FirstName= '{}', LastName = '{}', OnCampus= {},IsWorking={}, GPA={}
            Where Email = '{}';
        '''.format(firstname, lastname, oncampus, isworking, gpa, email))

    def get_student_info_by_instructor_id(self, instructor_id):
        self.my_cursor.execute('''
            SELECT CS.GradePercentage, S.GPA, S.IsWorking, S.OnCampus, S.InstitutionId
            FROM Instructor I
            JOIN CourseInstructor CI on CI.InstructorId = I.InstructorId
            JOIN CourseStudent CS on CS.CourseId = CI.CourseId
            JOIN Student S on S.StudentId = CS.StudentId
            WHERE I.InstructorId = {}
                '''.format(instructor_id))
        return self.my_cursor.fetchall()

    def get_instructor_info_by_id(self, instructor_id):
        self.my_cursor.execute('''
            SELECT I.*, C.CourseDept, C.CourseLevel
            FROM Instructor I
            JOIN CourseInstructor CI on CI.InstructorId = I.InstructorId
            JOIN Course C on C.CourseId = CI.CourseId
            Where I.InstructorId = {}
        '''.format(instructor_id))
        return self.my_cursor.fetchone()

    def get_course_info_by_id(self, course_id):
        self.my_cursor.execute('''
            SELECT C.CourseTypeId, C.CourseDept, C.CourseLevel, C.CreditHours, I.FirstName, I.LastName, I.IsTenured, I.YearsTeaching, I.Degree
            FROM Course C
            Join CourseInstructor CI on C.CourseId = CI.CourseId
            JOIN Instructor I on I.InstructorId = CI.InstructorId
            Where C.CourseId = {}
        '''.format(course_id))
        return self.my_cursor.fetchone()

    def get_student_info_by_activity_id(self, activity_id):
        self.my_cursor.execute('''
            SELECT COALESCE(AST.HasPosition, 0), S.GPA, S.OnCampus, S.IsWorking, S.InstitutionId, CS.GradePercentage
            FROM Activity A
            Join ActivityStudent AST on A.ActivityId = AST.ActivityId
            Join Student S on S.StudentId = AST.StudentId
            Join CourseStudent CS on CS.StudentId = S.StudentId
            Where A.ActivityId = {}
        '''.format(activity_id))
        return self.my_cursor.fetchall()

    def get_activity_info_by_id(self, activity_id):
        self.my_cursor.execute('''
            Select A.ActivityName
            From Activity A 
            Where A.ActivityId = {}
        '''.format(activity_id))
        return self.my_cursor.fetchone()

    def get_student_info_by_institution_id(self, institution_id):
        self.my_cursor.execute('''
            SELECT S.OnCampus, S.IsWorking, S.GPA, CS.GradePercentage, AST.HasPosition, C.CourseDept
            FROM Institution I
            JOIN Student S on S.InstitutionId = I.InstitutionId
            JOIN ActivityStudent AST on AST.StudentId = S.StudentId
            JOIN CourseStudent CS on CS.StudentId = S.StudentId
            JOIN Course C on C.CourseId = CS.CourseId
            WHERE I.InstitutionId = {}
        '''.format(institution_id))
        return self.my_cursor.fetchall()

    def get_institution_info_by_id(self, institution_id):
        self.my_cursor.execute('''
                    SELECT I.InstitutionName
                    FROM Institution I
                    WHERE I.InstitutionId = {}
                '''.format(institution_id))
        return self.my_cursor.fetchone()

    def delete_student_by_email(self, email):
        self.my_cursor.execute('''
            DELETE
            FROM Student
            WHERE Email = '{}'
        '''.format(email))
