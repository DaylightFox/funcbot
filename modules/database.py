import pymysql
import datetime

class Database():
    """
    Returns an object of *database*.
    """
    def __init__(self, username, password, host, db):
        # Establish connection to database
        try:
            self.cnx = pymysql.connect(user=username,
                                          password=password,
                                          host=host,
                                          database=db,
                                          charset='utf8mb4',
                                          cursorclass=pymysql.cursors.DictCursor)
            self.cursor = self.cnx.cursor()
        except Exception as err:
            print("Connection Failed!")
            print(err)
    
    # --------------
    # Server Queries
    # --------------
    def addServer(self, server):
        query = """INSERT INTO Servers (sid) 
                   VALUES (%s);"""
        self.cursor.execute(query, (server.id,))
        self.cnx.commit()
    
    def serverExists(self, server):
        query = """SELECT sid
                   FROM Servers
                   WHERE sid=%s;"""
        self.cursor.execute(query, (server.id,))
        result = self.cursor.fetchone()
        if result is None:
            return False
        else:
            return True
    
    def removeServer(self, server):
        query = """DELETE FROM Servers WHERE sid=%s;"""
        self.cursor.execute(query, (server.id,))
        self.cnx.commit()
        self.__cleanUsers(server)
    
    # --------------
    # Prefix Queries
    # --------------
    def getPrefix(self, server):
        query = """SELECT prefix FROM
                   Servers WHERE sid=%s"""
        self.cursor.execute(query, (server.id,))
        return(self.cursor.fetchone()['prefix'])
    
    def setPrefix(self, server, prefix):
        query = """UPDATE Servers SET prefix=%s WHERE sid=%s"""
        self.cursor.execute(query, (prefix, server.id))
        self.cnx.commit()
    
    # -------------------
    # Leaderboard Queries
    # -------------------
    def getTop(self, server):
        query = """SELECT Users.username, ServerUsers.score
                   FROM Users, ServerUsers
                   WHERE Users.uid=ServerUsers.uid
                   AND ServerUsers.sid=%s
                   ORDER BY score DESC
                   LIMIT 10"""
        self.cursor.execute(query, (server.id,))
        return(self.cursor.fetchall())
    
    def getUser(self, server, user):
        query = """SELECT Users.uid, Users.username, Users.profile_pic, ServerUsers.score
                   FROM Users, ServerUsers
                   WHERE Users.uid=ServerUsers.uid
                   AND ServerUsers.sid=%s
                   AND Users.uid=%s"""
        self.cursor.execute(query, (server.id, user.id))
        return(self.cursor.fetchone())
    
    def getRank(self, server, user):
        query = """SELECT uid, score
                   FROM ServerUsers
                   WHERE sid=%s
                   ORDER BY score DESC"""
        self.cursor.execute(query, (server.id,))
        results = self.cursor.fetchall()
        for c,i in enumerate(results):
            if i['uid'] == user.id:
                return(c+1)
    
    def upvoteUser(self, server, user):
        # First get the score
        query = """SELECT score
                   FROM ServerUsers
                   WHERE sid=%s
                   AND uid=%s"""
        self.cursor.execute(query, (server.id, user.id))
        result = self.cursor.fetchone()
        # If user isn't in table for server then score is 0
        if result is None:
            # Add user to ServerUsers
            self.__addUser(server, user)
            score = 0
        else:
            score = result['score']
        query = """UPDATE ServerUsers
                   SET score=%s
                   WHERE sid=%s
                   AND uid=%s"""
        self.cursor.execute(query, (score+1, server.id, user.id))
        self.cnx.commit()
    
    def setUpvoteTimer(self, server, user):
        # Check to see if user in ServerUsers
        query = """SELECT score
                   FROM ServerUsers
                   WHERE sid=%s
                   AND uid=%s"""
        self.cursor.execute(query, (server.id, user.id))
        result = self.cursor.fetchone()
        # If none, user not in ServerUsers
        if result is None:
            # Add user to ServerUsers
            self.__addUser(server, user)
        query = """UPDATE ServerUsers
                   SET last_upvote=%s
                   WHERE sid=%s
                   AND uid=%s"""
        time = datetime.datetime.now()
        self.cursor.execute(query, (time, server.id, user.id))
        self.cnx.commit()
    
    def __addUser(self, server, user):
        if self.userExists(user) == False:
            query = """INSERT INTO Users VALUES (%s, %s, %s)"""
            self.cursor.execute(query, (user.id, user.name, user.avatar_url))
            self.cnx.commit()
        query = """INSERT INTO ServerUsers (sid, uid, score)
                   VALUES (%s, %s, 0)"""
        self.cursor.execute(query, (server.id, user.id))
        self.cnx.commit()
    
    def userExists(self, user):
        query = """SELECT uid
                   FROM Users
                   WHERE uid=%s;"""
        self.cursor.execute(query, (user.id,))
        result = self.cursor.fetchone()
        if result is None:
            return False
        else:
            return True
    
    def userCanUpvote(self, server, user):
        query = """SELECT last_upvote
                   FROM ServerUsers
                   WHERE sid=%s
                   AND uid=%s"""
        self.cursor.execute(query, (server.id, user.id))
        result = self.cursor.fetchone()
        if result is None:
            self.__addUser(server, user)
        query = """SELECT last_upvote
                   FROM ServerUsers
                   WHERE sid=%s
                   AND uid=%s"""
        self.cursor.execute(query, (server.id, user.id))
        last_upvote = self.cursor.fetchone()['last_upvote']
        if last_upvote == None:
            return True
        time_diff = datetime.datetime.now() - last_upvote
        if time_diff > datetime.timedelta(hours=24):
            return True
        else:
            return False

    def getUpvoteTimer(self, server, user):
        query = """SELECT last_upvote
                   FROM ServerUsers
                   WHERE sid=%s
                   AND uid=%s"""
        self.cursor.execute(query, (server.id, user.id))
        result = self.cursor.fetchone()
        if result is None:
            self.__addUser(server, user)
            return(None)
        last_upvote = result['last_upvote']
        last_upvote = datetime.timedelta(hours=last_upvote.hour,
                                         minutes=last_upvote.minute,
                                         seconds=last_upvote.second)
        next_upvote = last_upvote + datetime.timedelta(hours=24)
        time_now = datetime.datetime.now()
        time_now = datetime.timedelta(hours=time_now.hour,
                                      minutes=time_now.minute,
                                      seconds=time_now.second)
        return(next_upvote - time_now)

    def removeUserFromServer(self, user, server):
        query = """DELETE FROM ServerUsers
                   WHERE sid=%s
                   AND uid=%s"""
        self.cursor.execute(query, (server.id, user.id))
        self.cnx.commit()
        self.__cleanUsers(server)

    def updateUser(self, user):
        query = """UPDATE Users SET username=%s, profile_pic=%s
                   WHERE uid=%s"""
        self.cursor.execute(query, (user.name, user.avatar_url, user.id))
        self.cnx.commit()

    # -------------
    # Watch Queries
    # -------------
    def getWatching(self, server):
        query = """SELECT Watchers.url
                   FROM Watchers, ServerWatchers
                   WHERE Watchers.wid=ServerWatchers.wid
                   AND ServerWatchers.sid=%s"""
        self.cursor.execute(query, (server.id,))
        return(self.cursor.fetchall())
    
    def whoWatches(self, wid):
        query = """SELECT sid, channel
                   FROM ServerWatchers
                   WHERE wid=%s"""
        self.cursor.execute(query, (wid))
        return(self.cursor.fetchall())
    
    def setWatching(self, server, url, channel, content):
        query = """INSERT INTO Watchers (url, content)
                   VALUES (%s, %s)"""
        self.cursor.execute(query, (url, content))
        query = """SELECT wid
                   FROM Watchers
                   WHERE url=%s"""
        self.cursor.execute(query, (url))
        wid = self.cursor.fetchone()['wid']
        query = """INSERT INTO ServerWatchers
                   VALUES (%s, %s, %s)"""
        self.cursor.execute(query, (server.id, wid, str(channel.created_at)))
        self.cnx.commit()
    
    def removeWatching(self, server, url):
        query = """SELECT wid
                   FROM Watchers
                   WHERE url=%s"""
        self.cursor.execute(query, (url))
        watchers = self.cursor.fetchall()
        if len(watchers) > 1:
            query = """DELETE FROM ServerWatchers
                       WHERE Watchers.wid=ServerWatchers.wid
                       AND ServerWatchers.sid=%s
                       AND Watchers.url=%s"""
            if type(server) is int:
                self.cursor.execute(query, (server, url))
            else:
                self.cursor.execute(query, (server.id, url))
            self.cnx.commit()
        elif len(watchers) == 1:
            query = """DELETE FROM Watchers
                       WHERE url=%s"""
            self.cursor.execute(query, (url,))
            self.cnx.commit()
        else:
            return
    
    def updateWatching(self, wid, content):
        query = """UPDATE Watchers
                   SET content=%s
                   WHERE wid=%s"""
        self.cursor.execute(query, (content, wid))
        self.cnx.commit()
    
    def getAllWatchURLs(self):
        query = """SELECT *
                   FROM Watchers"""
        self.cursor.execute(query)
        return(self.cursor.fetchall())
    
    # -------------
    # Limit Queries
    # -------------
    def setLimit(self, server, channel):
        if channel is None:
            query = """UPDATE Servers
                       SET command_limit=NULL
                       WHERE sid=%s"""
            self.cursor.execute(query, (server.id,))
        else:
            query = """UPDATE Servers
                       SET command_limit=%s
                       WHERE sid=%s"""
            self.cursor.execute(query, (channel.name, server.id))
        self.cnx.commit()
    
    def getLimit(self, server):
        query = """SELECT command_limit
                   FROM Servers
                   WHERE sid=%s"""
        self.cursor.execute(query, (server.id,))
        return(self.cursor.fetchone()['command_limit'])
        
    # ----------------
    # Clean Up Queries
    # ----------------
    def __cleanUsers(self, server):
        query = """SELECT Users.uid
                   FROM Users
                   WHERE NOT EXISTS (
                       SELECT ServerUsers.uid
                       FROM ServerUsers
                   )"""
        self.cursor.execute(query)
        users_without_server = self.cursor.fetchall()
        for user in users_without_server:
            query = """DELETE FROM Users
                       WHERE uid=%s"""
            self.cursor.execute(query, (user["uid"],))
        self.cnx.commit()
