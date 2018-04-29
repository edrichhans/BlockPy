import getpass
import hashlib
import random
import sys
import uuid

def ask_for_username():
    while True:
        print("Please enter the username you would like to use:")
        username = raw_input()
        return username


def ask_for_password(privilege = None):
    while True:
        print("What password would you like to create?")
        salt = uuid.uuid4().hex
        if privilege is None:
            password1 = hashlib.sha256(getpass.getpass()).hexdigest()
            print("\nPlease enter password again.")
            password2 = hashlib.sha256(getpass.getpass()).hexdigest()
        else:
            password1 = getpass.getpass()
            password2 = getpass.getpass()
        hashed_password1 = hashlib.sha256(salt + password1).hexdigest()
        hashed_password2 = hashlib.sha256(salt + password2).hexdigest()

        if hashed_password1 == hashed_password2:
            return hashed_password2, salt
        else:
            print("Your passwords do not match. Please retry")


def store_info(conn, cur, privelege = None):
    username = ask_for_username()
    hashed_pass, salt = ask_for_password(privilege)
    if privilege is None:
        privilege = 1
    #Database integration
    try:
        insertSql = '''INSERT INTO users ("username", "password_hash", "salt", "privelege")
            VALUES(%s, %s, %s, %s);'''
        cur.execute(insertSql,(username, hashed_pass, salt, privelege))
        conn.commit()
    except psycopg2.ProgrammingError as error:
        print error


def find_hashed_password_by_user(username, password, conn, cur, privelege = None):
    print "Verifying from database...."
    if privelege is None:
        privelege = 1
    try:
        querySql = 'SELECT * FROM users WHERE username = %s AND privelege = %s'
        cur.execute(querySql, (username,privelege))
        user = cur.fetchone()
    except psycopg2.ProgrammingError as error:
        print error
    # print elements
    if not user:
        print "Incorrect User/Password."
    else:
        if user[0] == username:
            hashed_password = hashlib.sha256(user[2].strip() + password).hexdigest()
            return user[1] == hashed_password
        else:
            print "Incorrect User/Password."
            return False

def checkIfUsersExist(conn, cur):
    createTableSql = 'CREATE TABLE IF NOT EXISTS users(username TEXT PRIMARY KEY, password_hash TEXT NOT NULL, salt TEXT NOT NULL, privelege INTEGER NOT NULL);'
    cur.execute(createTableSql)
    conn.commit()

def checkIfAdminExist(conn, cur):
    try:
        querySql = 'SELECT * FROM users WHERE username = %s'
        cur.execute(querySql, ("admin",))
        user = cur.fetchone()
    except psycopg2.ProgrammingError as error:
        print error
    if not user:
        print "Admin does not exist, please enter desired credentials for admin:"
        store_info(conn, cur, 0)


def dropUsers(conn, cur):
    deleteTableSql = 'DROP TABLE IF EXISTS users;'
    cur.execute(deleteTableSql)
    conn.commit()


# if __name__ == "__main__":
    #For storing new usernames and passwords
    # username = ask_for_username()
    # hashedPass, salt = ask_for_password()
    # store_info(username, hashedPass, salt)
    #Insert the following lines of code to implement login verification:
    # while find_hashed_password_by_user(ask_for_username()) != True:
        # print "Username or Password is Incorrect. Please try again."
    # print "Login Successful"