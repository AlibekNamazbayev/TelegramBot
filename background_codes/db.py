import cx_Oracle 


class CXOracle:

    def __init__(self, username, password):

        self.connection = cx_Oracle.connect('{}/{}@localhost'.format(username, password))
        self.cursor = self.connection.cursor()


    def select_cities(self):
        """ Получаем все строки """
        with self.connection:
            return self.cursor.execute('SELECT * FROM cities').fetchall()

    def select_city(self, city):
        """ Получаем все строки """
        with self.connection:
            return self.cursor.execute('SELECT * FROM cities WHERE ID = ? ', (city,)).fetchall()[0]

    def select_subject(self, subject):
        """ Получаем все строки """
        with self.connection:
            return self.cursor.execute('SELECT * FROM subjects WHERE ID = ? ', (subject,)).fetchall()[0]

    def select_subjects(self):
        """ Получаем все строки """
        with self.connection:
            return self.cursor.execute('SELECT * FROM subjects').fetchall()

    def select_university_specialty(self, uni_lang, name_lang, city, score, subject, fininfo):
        """ Получаем одну строку с номером rownum """
        with self.connection:
            st = '''SELECT univercity.{}, specialties.{},
                specialties.sub_id, univercity.city_id FROM uni_spe 
                INNER JOIN univercity ON uni_spe.uni_id=univercity.id 
                INNER JOIN specialties ON uni_spe.spe_id=specialties.code
                WHERE sub_id={} and city_id={}'''.format(str(uni_lang), str(name_lang), str(subject), str(city))
            return self.cursor.execute(st).fetchall()

    def select_single_specialty(self, rownum):
        """ Получаем одну строку с номером rownum """
        with self.connection:
            return self.cursor.execute('SELECT * FROM specialties WHERE id = ?', (rownum,)).fetchall()[0]

    def count_universities(self):
        """ Считаем количество строк """
        with self.connection:
            result = self.cursor.execute('SELECT * FROM universities').fetchall()
            return len(result)

    def close(self):
        """ Закрываем текущее соединение с БД """
        self.connection.close()
