import getpass, hashlib, random, sys, uuid, psycopg2
from blockpy_logging import logger

def ask_for_username():
    while True:
        print("Please enter the username you would like to use:")
        username = raw_input()
        return username


def ask_for_password():
    while True:
        print("What password would you like to create?")
        salt = uuid.uuid4().hex
        hashed_password1 = hashlib.sha256(salt + getpass.getpass()).hexdigest()
        print("\nPlease enter password again.")
        hashed_password2 = hashlib.sha256(salt + getpass.getpass()).hexdigest()

        if hashed_password1 == hashed_password2:
            return hashed_password2, salt
        else:
            print("Your passwords do not match. Please retry")


def store_info(conn, cur, privilege = None):
    username = ask_for_username()
    hashed_pass, salt = ask_for_password()
    if privilege is None:
        privilege = 1
    #Database integration
    try:
        insertSql = '''INSERT INTO users ("username", "password_hash", "salt", "privilege")
            VALUES(%s, %s, %s, %s);'''
        cur.execute(insertSql,(username, hashed_pass, salt, privilege))
        conn.commit()
        logger.info('User Created',
            extra={'username':username, 'privilege': privilege})
    except psycopg2.ProgrammingError as error:
        print error


def find_hashed_password_by_user(username, password, conn, cur, privilege = None):
    print "Verifying from database...."
    if privilege is None:
        privilege = 1
    try:
        querySql = 'SELECT * FROM users WHERE username = %s AND privilege = %s'
        cur.execute(querySql, (username,privilege))
        user = cur.fetchone()
    except psycopg2.ProgrammingError as error:
        print error
    # print elements
    if not user:
        print "Incorrect User/Password."
        logger.warn('Invalid Login',
            extra={'username':username, 'privilege':privilege})
        return False
    else:
        if user[0] == username:
            hashed_password = hashlib.sha256(user[2].strip() + password).hexdigest()
            logger.info('Login successful',
                extra={'username':username, 'privilege':privilege})
            return user[1] == hashed_password
        else:
            print "Incorrect User/Password."
            logger.warn('Invalid Login',
                extra={'username':username, 'privilege':privilege})
            return False

def checkIfUsersExist(conn, cur):
    createTableSql = 'CREATE TABLE IF NOT EXISTS users(username TEXT PRIMARY KEY, password_hash TEXT NOT NULL, salt TEXT NOT NULL, privilege INTEGER NOT NULL);'
    cur.execute(createTableSql)
    conn.commit()
    logger.info('Users table created')

def checkIfAdminExist(conn, cur):
    try:
        querySql = 'SELECT * FROM users WHERE username = %s'
        cur.execute(querySql, ("admin",))
        user = cur.fetchone()
    except psycopg2.ProgrammingError as error:
        print error

    try:
        if not user:
            print "Admin does not exist, please enter desired credentials for admin:"
            logger.info('Admin does not exist!')
            store_info(conn, cur, 0)
    except Exception as e:
        print e


def dropUsers(conn, cur):
    deleteTableSql = 'DROP TABLE IF EXISTS users;'
    cur.execute(deleteTableSql)
    conn.commit()
    logger.info('Table users dropped')


# if __name__ == "__main__":
    #For storing new usernames and passwords
    # username = ask_for_username()
    # hashedPass, salt = ask_for_password()
    # store_info(username, hashedPass, salt)
    #Insert the following lines of code to implement login verification:
    # while find_hashed_password_by_user(ask_for_username()) != True:
        # print "Username or Password is Incorrect. Please try again."
    # print "Login Successful"
