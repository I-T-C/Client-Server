from socket import socket, AF_INET, SOCK_STREAM, SOL_SOCKET, SO_REUSEADDR
import time
import pickle
from threading import Thread

'''
    This is the server class it handles everything on the server side.
'''

class ServerTcp():
    def __init__(self):
        '''
            This is the initializer '__init__' method. When i create an instance of the class
            at the bottom of the file, this method is automatically called and it just initializes
            some variables so we can access them throughout the class. the variables with self. in-front
            of them are like global variables accessible from anywhere in the ServerTcp class.
        '''

        self.host = '' # If this doesnt work try gethostname()
        self.port = 5001
        self.soc = socket(AF_INET, SOCK_STREAM)
        self.soc.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.startTime = time.ctime()
        
        self.usersLoggedOn = [] # This is a list used to track users that are currently logged on
        self.connections = [] # Each client thread is stored in a list.

    def start(self):
        print("Server started on: {}".format(self.startTime))
        '''
            This method opens the socket and accepts client connections.
            When a client connects inside the while True: block, a new thread
            is created and the clients connection is passed on to the main client
            function tcpLink() which will handle authorising the user and so on.
        '''
        self.soc.bind((self.host, self.port))
        self.soc.listen(10)
        print("socket created...")

        while True:
            print("\nwaiting for a client to connect...\n")
            con, addr = self.soc.accept()
            """When a client connects, they are given a thread and they begin authorisation in the tcp_link() function."""
            t = Thread(target=self.tcp_link, args=(con, addr))
            t.start()
            self.connections.append(t)

    def tcp_link(self, con, address):
        userAuthorised = False # When the user logs on successfully, this will be set to true. Used as a control statement throughout the function.
        user = []
        print("Connection from: %s" % str(address))
        '''
            This is the main client function. When a client connects, 
            the server will immediately attempt to authorise the user.    
        '''
        for i in range(3): # Run the authentication attempt 3 times in a for loop
            attempt = self.read_msg(con) # Waiting for the client to send their username and password attempt
            """ Pass the attempt to the check_credentials() function,
                if the username and password match it returns True """

            attemptAuthorised = self.check_credentials(attempt) # True if the user is in the text file
            
            """  If the user is already logged on they will be rejected access.
                 This piece of code will build a response to send back to the client.
                 There are 3 possible responses. 0, 1 and 2.

                 0 = [unsuccessful] username and password were not found
                 1 = [unsuccessful] username and password found but the user is logged on
                 2 = [success] username and password found and the user isn't logged on 
            """
            result = 0 # initialise the result to 0
            if attemptAuthorised: # True is the username and password were correct
                result = 1 # The result is set to 1
                """ We need to check if the user is already logged on. """
                if attempt not in self.usersLoggedOn: # If the user isn't stored in the list of logged on users
                    userAuthorised = True # Set this variable to true, we will use this to break out of the for loop
                    result = 2 # The result is set to 2, this will be transmitted to the client alloowing them access
                    user = attempt # Store the correct attempt in a list
                    self.usersLoggedOn.append(user) # appent the correct attempt to the list of users logged on, they will fail this check next time...

            self.write_msg(con, result) # Send the result to the client to process the result and react accordingly.

            if userAuthorised: # This is set to true when the client is logged on successfully, no need to authorise them anymore
                break

        if userAuthorised: # The user has been authorised, wait for instructions...
            print("\n%s authenticated.\n" % str(user))

            quitList = ['q', 'quit', 'exit', '5'] # List of commands the client can use to close the connection
    
            while True:
                # The user has been authorised, they now have access to our servers records. 
                msg = self.read_msg(con)

                if msg == False:    # When a client disconnects abruptly the server will log the user off and break the loop
                    self.quit_program(user, con)
                    print("\n")
                    print("{} disconnected abruptly!".format(user[0]))
                    print("cleaning up users login details and closing the socket")
                    print("{} has now been logged off gracefully.".format(user[0]))
                    break

                if msg == '1':
                    self.get_server_name_and_ip(con)

                elif msg == '2':
                    self.get_statistics(con)

                elif msg == '3':
                    self.add_new_organisation(con)

                elif msg == '4':
                    self.remove_organisation(con)

                elif msg in quitList:
                    self.quit_program(user, con)
                    break

        print("{} disconnected at {}".format(address, time.ctime()))

    def get_server_name_and_ip(self, con):
        self.write_msg(con, "1OK")
        request = self.read_msg(con)
        serverNameAndIp = []
        organisations = []
        try:
            f = open("organisations.txt", 'r')
            raw = f.readlines()
            f.close()
            for organisation in raw:
                organisations.append(organisation.split())
        except IOError:
            print("File not found")
            self.write_msg(con, "We are sorry for any inconvenience our servers are down :(")
        else:
            print(organisations)
            for organisation in organisations:
                if organisation[0].lower() == request.lower():
                    serverNameAndIp = [organisation[1], organisation[2]]

            if len(serverNameAndIp) > 1:
                self.write_msg(con, serverNameAndIp)
            else:
                self.write_msg(con, "Organisation not listed...")

    def get_statistics(self, con):

        self.write_msg(con, "2OK") # Acknowledgment from server to client.

        """ The client has requested the server uptime statistics. The first thing we have to do is open the file 
            and make a seperate list of uptimes.
        """
        organisations = self.get_file_as_list("organisations.txt") # Retrieve the file using function get_file_as_list()

        uptimes = []
        # Initialise an empty array to store the server uptimes

        for organisation in organisations:  # Iterate the organisations file and append the 4th element (uptime) to the uptimes[] array
            try:
                if organisation[3].isdigit():
                    uptimes.append(int(organisation[3])) # Cast the string to an integer and append it to the new uptimes list.
            
            except IndexError:
                print("organisations file is dirty")


        uptimes.sort()  # Sort the list in ascending order

        """ Calculate the average """
        total = 0

        for uptime in uptimes:
            total += uptime

        average = total / len(uptimes)

        """ Calculate the median """
        ''' 
            If the # of elements in the list is a even one
            there is no "middle". Instead a "mean" is calculated
            from the upper-middle and lower-middle elements.
        '''
        if len(uptimes) % 2 == 0: # Is the length of the array an even number?
            idx1 = (len(uptimes) / 2) - 1
            idx2 = (len(uptimes) / 2)
            num1 = uptimes[int(idx1)]
            num2 = uptimes[int(idx2)]
            median = (num1 + num2) / 2
        else:
            idx = ((len(uptimes) + 1) / 2) - 1
            median = uptimes[int(idx)]

        """ Calculate the minimum and the maximum """
        low = uptimes[0]
        high = uptimes[len(uptimes) - 1]

        for uptime in uptimes:
            if uptime > high:
                high = uptime
            if uptime < low:
                low = uptime

        """ Calculate the Mode """
        # ToDo: Calculate the mode...

        """ Build a report and send it to the client """

        rep = '{:*^36}\n'.format('')
        rep += '{:^36}\n'.format('Uptime Statistics Report')
        rep += '{:*^36}\n'.format('')
        rep += '{:18}'.format('Mean:')
        rep += '{:>18}\n'.format(round(average, 2))
        rep += '{:18}'.format("Median:")
        rep += '{:>18}\n'.format(median)
        rep += '{:18}'.format("Minimum:")
        rep += '{:>18}\n'.format(low)
        rep += '{:18}'.format("Maximum:")
        rep += '{:>18}\n'.format(high)

        self.write_msg(con, rep) # Send report

    def add_new_organisation(self, con):
        switch = True
        self.write_msg(con, "3OK")
        orgList = self.read_msg(con)
    
        organisations = self.get_file_as_list("organisations.txt")

        for organisation in organisations:
            if organisation[0].lower() == orgList[0].lower():
                switch = False
                break

        if switch:
            self.write_msg(con, "adding the organisation...")

            orgStr = "{0}\t\t\t{1}\t\t\t{2}\t\t\t{3}\n".format(orgList[0], orgList[1], orgList[2], orgList[3])
            print(orgStr)
            with open("organisations.txt", 'a') as f:
                f.write(str(orgStr))
                f.close()
                print("Organisation has been successfully added ")

        else:
            self.write_msg(con, "organisation already exists...")

    def remove_organisation(self, con):
        switch = False
        org = []
        self.write_msg(con, "4OK")
        organisations = self.get_file_as_list("organisations.txt")
        removeOrg = self.read_msg(con)

        for organisation in organisations:
            if organisation[0].lower() == removeOrg.lower():
                switch = True
                org = organisation

        if switch:
            self.write_msg(con, org)
            response = self.read_msg(con)

            try:
                f = open("organisations.txt", 'r')
                lines = f.readlines()
            except:
                print("error...")

            if response == 'y':

                with open("organisations.txt", 'w') as f:
                    for organisation in lines:

                        if organisation.find(removeOrg) == -1:
                            f.write(organisation)

                self.write_msg(con, "the organisation has been removed")
            elif response == 'n':
                self.write_msg(con, "Organisation preserved...")



    def quit_program(self, user, con):
        self.usersLoggedOn.remove(user) # Remove the user from the currently logged on list.
        con.close() # Close the clients connection...

    def check_credentials(self, attempt):
        '''
            This function accepts one argument. When a client attempts to login
            the username and password will be passed through as a list named "attempt"
            The function opents the users.txt file, and attempts to match a username and password
            if the attempt is successful the function returns true.AF_INET
        '''
        authList = self.get_file_as_list("users.txt") # Get the users.txt file and store it in authList (The file has been converted to a list)
        #print(authList)
        
        if attempt in authList: # If the attempt is is the list of users return True.
            return True
        else: # The username and password were not found...
            return False
    """
        read_msg accepts one argument. Each time a message is sent to the client it is passed to this function
        the data is deserialized (converted back to whatever it was before if was transmited) and returned to 
        the calling statement. All exceptions are handled inside of the function.
    """
    def read_msg(self, con):
        try:
            data = con.recv(1024) # Recieve data from the client
        except socket.Error as e: 
            print("ERROR [read_msg]: %s" % str(e))
        else:
            try:
                msg = pickle.loads(data)
            except Exception as e:
                print("Error [read_msg.pickle]: %s" % str(e))
                return False
            else:
                return msg
    
    """ 
        write_msg takes two arguments, a socket, 
        and an object that gets serialised and 
        sent over the network
    """
    def write_msg(self, con, msg):
        try:
            data = pickle.dumps(msg)
            con.send(data)
            print("Sent: '%s'" % msg)
        except Exception as e:
            print("ERROR [write_msg] %s " % str(e))


    def get_file_as_list(self, filename):

        lines = []
        '''
            This function opens the file, creates a list out of the contents
            and returns the list to the caller
        '''
        try:
            f = open(filename, 'r')
        except IOError:
            print("Cannot find/read the file.")
        else:
            raw = f.readlines()
            f.close()
            for line in raw:
                lines.append(line.split())
                #lines = list(map(str.split, raw))   
            return lines
            

'''
    The end of the ServerTcp() class. 
'''

server = ServerTcp()    # Create an instance of the ServerTcp() class

server.start()          # Run the start method.
