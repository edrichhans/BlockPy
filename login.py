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
    line = password_file.readline()
    elements = line.split('|')
    while line:
        print type(elements[0])
        print "is"
        print type(username)
        if elements[0] == username:
            print "here"
            return elements
        line = password_file.readline()
        elements=line.split('|')


if __name__ == "__main__":
    username = ask_for_username()
    hashedPass, salt = ask_for_password()
    print find_hashed_password_by_user(username)[1]
