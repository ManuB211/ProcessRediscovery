import json
import math

class AbstractRepresentation:

    def __init__(self):
        self.tasks = []
        self.taskCount = {}
        self.instanceCount = {}
        self.directSuccession = {}
        self.X = {}
        self.X_Da = {}
        self.i = 0
        #self.i_Da = 0
        self.k = 0
        self.delta = 0
        self.isLossy = False
        self.isSpaceSaving = False
        self.model = ""

        #To be able to compute repetition count
        self.lastTwoEventsPerInstance = {}
        self.repetitionCount = {}

        #so that graph shows only the activities, but on click the label is shown
        self.mapActivityToLabel = {}
        #For the timestamps (earliest, latest, median, average)
        self.eventTimes = {}

        #To handle the different modes for when petri net is generated
        self.amountEventsReceived = 0

        #Flag to determine if the datastructures should be used or if event traces shall be logged from the event stream
        self.useExperimental = False

        #In case classic fodina is used, this map stores the event traces per instance
        self.eventTraces = {}

    #Setters for the attributes that need to be set from the outside
    def setLossy(self):
        self.isLossy = True

    def setSpaceSaving(self):
        self.isSpaceSaving = True

    def setModel(self,pModel):
        self.model = pModel

    def setK(self, maxSize):
        self.k = maxSize

    def setUseExperimental(self, pUseExperimental):
        self.useExperimental = pUseExperimental

    #Returns the event traces in the required format (array of arrays of strings)
    def getEventTraces(self):
        rst = []

        for eventTrace in self.eventTraces.values():
            eventTraceSortedByTimestamp = sorted(eventTrace, key=lambda x : x[1])
            rst.append([item[0] for item in eventTraceSortedByTimestamp])

        return rst


    def newEvent(self, postData):
        postDataDecoded = postData.decode() 
    
        #Trim all irrelevant data from the event, so that it can be parsed directly to a JSON
        indexStart = postDataDecoded.index('{')
        indexEnd = postDataDecoded.index('--Time_is_an_illusion._Lunchtime_doubly_so.0xriddldata--')

        postDataJson = json.loads(postDataDecoded[indexStart:indexEnd])

        #TODO? Implement functionality to abandon an instance when execution is stopped
        #Filter out only the events that belong to the model that was started. Otherwise other longrunning models might still send events which will be included as well and cause a mixup
        modelName = postDataJson['instance-name']
        label = postDataJson['content']['label']

        #Treat events only if its label isnt empty and if the event belongs to the last started instance (mixup with long-running other instances)
        if(modelName == self.model and label != ''):
            print(postDataJson)

            #Extract instance id, activity name and timestamp from received event
            instanceID = postDataJson['instance']
            activity = postDataJson['content']['activity']
            eventTimeCurr = postDataJson['timestamp']

            #log the time when the event occured
            if(activity not in self.eventTimes):
                self.eventTimes[activity] = []

            self.eventTimes[activity].append(eventTimeCurr)

            #If activity has been seen for the first time store mapping label<->activity
            if(activity not in self.mapActivityToLabel):
                self.mapActivityToLabel[activity] = label

            #Add activity to seen tasks or increment the count for the activity
            if activity not in self.tasks:
                    self.tasks.append(activity)
                    self.taskCount[activity] = 1
            else:
                self.taskCount[activity] += 1   

            #Decide between datastructure and creating event traces
            if(self.useExperimental):
                self.newEventExperimental(instanceID, activity)
            else:
                self.newEventClassicFodina(instanceID, activity, eventTimeCurr)

            #Store last two elements and see if repetition count needs to be updated for new event
            if(instanceID not in self.lastTwoEventsPerInstance):
                self.lastTwoEventsPerInstance[instanceID] = []

            #If length is two, check if the first element is equal to the new one, in which case the repetition count needs to be updated.
            lastTwoEventsForThisInstance = self.lastTwoEventsPerInstance[instanceID]
            if(len(lastTwoEventsForThisInstance) == 2):

                #Found a match, last three events (including new one) were X Y X
                if(lastTwoEventsForThisInstance[0] == activity):

                    repCountToInc = (lastTwoEventsForThisInstance[0], lastTwoEventsForThisInstance[1])

                    if(repCountToInc in self.repetitionCount):
                        self.repetitionCount[repCountToInc] += 1
                    else:
                        self.repetitionCount[repCountToInc] = 1

                #Remove the first 
                self.lastTwoEventsPerInstance[instanceID].pop(0)

            self.lastTwoEventsPerInstance[instanceID].append(activity)

    #EventTime has to be given as well, because there were instances, where an event a was triggered before (according to the timestamp) an event b, but b was received before a
    #Therefore the timestamp is stored with the event in the eventTrace and before it is used to generate the process model, the traces gets sorted by timestamp
    def newEventClassicFodina(self, instanceID, activity, eventTime):

        if(instanceID not in self.eventTraces):
            self.eventTraces[instanceID] = []

        self.eventTraces[instanceID].append((activity, eventTime))

        self.amountEventsReceived += 1


    def newEventExperimental(self, instanceID, activity):

        #Lossy and SpaceSaving Pseudo Code Line 3
        self.i += 1

        #Lossy and SpaceSaving Pseudo Code Line 5
        if(instanceID in self.X):
            #Lossy and SpaceSaving Pseudo Code Line 6
            self.instanceCount[instanceID] += 1

            #Lossy and SpaceSaving Pseudo Code Line 7
            self.addToDA(self.X[instanceID], activity)
                
            #Lossy and SpaceSaving Pseudo Code Line 8
            self.X[instanceID] = activity
        else:
            self.instanceCount[instanceID] = 1

            if(self.isSpaceSaving):

                #Space Saving Pseudo Code Line 9
                if(len(self.X) < self.k):
                    #Space Saving Pseudo Code Line 10
                    self.X[instanceID] = activity
                    #Space Saving Pseudo Code Line 11
                    self.instanceCount[instanceID] = 1

                else:
                    #Find instance with min count and remove its last seen element (Space Saving Pseudo Code Line 13)
                    currMin = 69420 #hopefully high enough 
                    currMinInstanceID = 0

                    for instance in self.instanceCount:
                        if(self.instanceCount[instance] < currMin):
                            currMin = self.instanceCount[instance]
                            currMinInstanceID = instance

                    #Space Saving Pseudo Code Line 14
                    self.instanceCount[instanceID] = self.instanceCount[currMinInstanceID] + 1

                    #Space Saving Pseudo Code Line 15
                    self.X.pop(currMinInstanceID)
                    self.X[instanceID] = activity

            elif(self.isLossy):
                #Lossy Pseudo Code Line 10
                self.X[instanceID] = activity

                #Lossy Pseudo Code Line 11
                self.instanceCount[instanceID] = self.delta


            #Should never happen, as either isLossy or isSpaceSaving is set each time
            else:
                print('Something went terribly wrong here')

            

        #Lossy Pseudo Code Line 12
        if(self.isLossy and math.floor(self.i / self.k) != self.delta):

            #Lossy Pseudo Code Line 13
            for instanceID in self.instanceCount:

                #Lossy Pseudo Code Line 14
                if(self.instanceCount[instanceID] <= self.delta):

                    #Lossy Pseudo Code Line 15
                    self.X.pop(instanceID)

            #Lossy Pseudo Code Line 16
            self.delta = math.floor(self.i / self.k) 



        self.amountEventsReceived += 1

    def addToDA(self, pre, succ):

        newRel = (pre,succ)

        #Frequent Pseudo Code Line 5
        if(newRel in self.X_Da):

            #Frequent Pseudo Code Line 6
            self.X_Da[newRel] += 1

        else:
            #Frequent Pseudo Code Line 7
            if(len(self.X_Da) < self.k):

                #Frequent Pseudo Code Line 8+9
                self.X_Da[newRel] = 1
            else:
                #Frequent Pseudo Code Line 11 (copy because of concurrent modification issue)
                for rel in self.X_Da.copy():
                    #Frequent Pseudo Code Line 12
                    self.X_Da[rel] -=1

                    #Frequent Pseudo Code Line 13
                    if(self.X_Da[rel] == 0):
                        #Frequent Pseudo Code Line 14
                        self.X_Da.pop(rel)
