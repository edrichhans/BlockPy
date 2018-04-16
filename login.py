import getpass
import hashlib
import random
import sys
import uuid


def open_pass_file():
    try:
        password_file = open('hashwork.txt', 'a+')
        return password_file
    except IOError as e:
        print("I/O Error({0}): {1}".format(e.errno, e.strerror))
        sys.exit()

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


def store_info(username, hashed_pass, salt):
    password_file = open_pass_file()
    password_file.write(username + " | " + hashed_pass + " | " + salt + "\n")

def find_hashed_password_by_user(username):
    password_file = open_pass_file()
    line = password_file.readline().replace(" ", "")
    elements = line.split('|')
    # print elements
    while line:
        if elements[0] == username:
            print("\nPlease enter password: ")
            hashed_password = hashlib.sha256(elements[2].strip() + getpass.getpass()).hexdigest()
            return elements[1] == hashed_password
        line = password_file.readline().replace(" ", "")
        elements=line.split('|')
    return False


if __name__ == "__main__":
    #For storing new usernames and passwords
    username = ask_for_username()
    hashedPass, salt = ask_for_password()
    store_info(username, hashedPass, salt)
    #Insert the following lines of code to implement login verification:
    # while find_hashed_password_by_user(ask_for_username()) != True:
        # print "Username or Password is Incorrect. Please try again."
    # print "Login Successful"
