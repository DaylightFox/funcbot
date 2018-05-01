CREATE TABLE IF NOT EXISTS Servers (sid VARCHAR(255) UNIQUE NOT NULL,
                                    prefix VARCHAR(255) DEFAULT 'f.',
                                    command_limit VARCHAR(255) DEFAULT NULL,
                                    PRIMARY KEY (sid));
CREATE TABLE IF NOT EXISTS Users (uid VARCHAR(255) UNIQUE NOT NULL,
                                  username VARCHAR(255),
                                  profile_pic TEXT,
                                  PRIMARY KEY (UID));
CREATE TABLE IF NOT EXISTS Watchers (wid INT(11) UNIQUE AUTO_INCREMENT,
                                     url TEXT NOT NULL,
                                     content TEXT NOT NULL,
                                     PRIMARY KEY (wid));
CREATE TABLE IF NOT EXISTS ServerUsers (sid VARCHAR(255) NOT NULL,
                                        uid VARCHAR(255) NOT NULL,
                                        score int(11) DEFAULT 0,
                                        last_upvote DATETIME,
                                        FOREIGN KEY (sid) REFERENCES Servers(sid) ON DELETE CASCADE,
                                        FOREIGN KEY (uid) REFERENCES Users(uid) ON DELETE CASCADE);
CREATE TABLE IF NOT EXISTS ServerWatchers (sid VARCHAR(255) NOT NULL,
                                           wid INT(11) NOT NULL,
                                           channel VARCHAR(255) NOT NULL,
                                           FOREIGN KEY (sid) REFERENCES Servers(sid) ON DELETE CASCADE,
                                           FOREIGN KEY (wid) REFERENCES Watchers(wid) ON DELETE CASCADE);