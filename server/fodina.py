from collections import Counter
from datetime import datetime, timedelta
import pygraphviz as pgv

#TODO: Weg
import random


class FodinaStream:
    #TODO: Change name of input_set
    def __init__(self, pConfiguration, pDirectSuccession, pRepetitionCount, pTasks, pTaskCount, pEventTimes, pMapActivityToLabel):
        self.configuration = pConfiguration
        self.directSuccession = pDirectSuccession
        self.repetitionCount = pRepetitionCount
        self.tasks = pTasks
        self.taskCount = pTaskCount
        self.eventTimes = pEventTimes
        self.mapActivityToLabel = pMapActivityToLabel

        self.dependencyGraphViz = pgv.AGraph(directed=True) 
        self.startTask = ""
        self.endTask = ""
        self.inputBindings = {}
        self.outputBindings = {}
        self.petriNet = pgv.AGraph(directed=True)

    def runFodinaStream(self):
        #Step 1 Convert to Taks Log; mine duplicates -> disabled for the use case

        #Step 2 is already done using the abstract representation

        #Step 3: Construct basic dependency graph using dependency measures
        self.dependencyGraphViz = constructBasicDependencyGraph(self.tasks, self.dependencyGraphViz, self.directSuccession, self.repetitionCount, self.configuration.td, self.configuration.tl1l, self.configuration.tl2l, self.configuration.noL2LWithL1l)

      #print(self.dependencyGraphViz)

        #Step 4: Set start and end task -> Done for the stream version via the times an event has occured 
        self.setStartAndEndTask()

        #Step 5
        if(self.configuration.noBinaryConflicts):
            self.dependencyGraphViz = resolveBinaryConflicts(self.dependencyGraphViz, self.repetitionCount, self.tasks)

        #Step 6
        if(self.configuration.connectNet and len(self.dependencyGraphViz.nodes()) > 0):
            self.dependencyGraphViz = assureReachability(self.directSuccession, self.startTask, self.endTask, self.dependencyGraphViz, self.tasks)


        #Step 7: Mine Long Distance Dependencies -> Disabled for now 

        #Step 8 (mine Split and Join Semantics)
        # for task in self.tasks:
        #     inputBindingsCurr = self.findPatterns(task, 'input')
        #     outputBindingsCurr = self.findPatterns(task, 'output')

        #     # print()
        #     # print('InputBindings for '+task)
        #     # print(inputBindingsCurr)
        #     # print()
        #     # print('OutputBindings for '+task)
        #     # print(outputBindingsCurr)


        #     self.inputBindings[task] = inputBindingsCurr
        #     self.outputBindings[task] = outputBindingsCurr

        # #From Input-/Output-Bindings construct Petri Net
        # self.constructPetriNet()

        self.enrichDependencyGraph()

    """
    Enrich the stream-based version (dependency Graph) with event data. 
    For the classic Fodina this is done during the creation of the petri net, but as that step is missing here, it is done separately
    """
    def enrichDependencyGraph(self):

        rst = pgv.AGraph(directed=True) 

        for edge in self.dependencyGraphViz.edges():
            startNode = edge[0]
            sinkNode = edge[1]
            
            if(not(rst.has_node(startNode))):
                rst.add_node(startNode, eventInfo=computeEventInfo(startNode, self.eventTimes, self.mapActivityToLabel))

            if(not(rst.has_node(sinkNode))):
                rst.add_node(sinkNode, eventInfo=computeEventInfo(sinkNode, self.eventTimes, self.mapActivityToLabel))

            if(not(rst.has_edge(edge))):
                rst.add_edge(edge)

        self.dependencyGraphViz = rst

        self.dependencyGraphViz.layout(prog="circo")
        self.dependencyGraphViz.draw('results/dependencyGraph.png')


        
    """
    Step 4: Fodina Algorithm
    For the stream-based version it is done using the event times (the first one received will be start, the latest one end) 
    """
    def setStartAndEndTask(self):

        #Set the first and last time of the first element in the dict as candidate
        firstKeyEventTimes = list(self.eventTimes.keys())[0]

        candidateTimeStart = datetime.fromisoformat(self.eventTimes[firstKeyEventTimes][0])
        candidateActivityStart = firstKeyEventTimes
        candidateTimeEnd = datetime.fromisoformat(self.eventTimes[firstKeyEventTimes][-1])
        candidateActivityEnd = firstKeyEventTimes

        for activity in self.eventTimes:
            first = datetime.fromisoformat(self.eventTimes[activity][0])
            last = datetime.fromisoformat(self.eventTimes[activity][-1])
            if(first < candidateTimeStart):
                candidateTimeStart = first
                candidateActivityStart = activity

            if(last > candidateTimeEnd):
                candidateTimeEnd = last
                candidateActivityEnd = activity

        self.startTask = candidateActivityStart
        self.endTask = candidateActivityEnd

        #Throw out edges (x,start) and (end, x)
        edgesToRemove = []

        for edge in self.dependencyGraphViz.edges():
            source = edge[0]
            sink = edge[1]

            if(source == self.endTask or sink == self.startTask):
                edgesToRemove.append(edge)

        for edgeToRemove in edgesToRemove:
            self.dependencyGraphViz.remove_edge(edgeToRemove)

    """
    See Comment on the FodinaClassic. Sadly didnt finish in time. 
    The idea for implementing that would be as follows: 

    The Abstract Representation stores for each already seen event an excerpt of the event trace that was received over the event stream, containing at max two of the key events. Once the third of the same kind is received, everything before the second can be deleted.

    When a run of the Fodina Algorithm is started then, the findPatterns method can find all the input/output patterns that are "new" for each of the events in the similar fashion it does anyway. 

    Example: Consider event Stream S = < a,b,c,a,d,e,a>

    For each of the possible occurences of events the algorithm is able to find new patterns. S is the event trace stored for event a

    S = <a,b>: Input patterns trivial, as no event preceding a, Output patterns can be computed looking at event trace from a to end
    S = <a,b,c>: Input patterns trivial, Output patterns: look from a to end
    S = <a,b,c,a> Input patterns: backtrace from secong a to first, output patterns: look from first a to second a
    S = <a,b,c,a,d> Input patterns: backtrace from second a to first, output patterns: first a to second a, second a to end
    S = <a,b,c,a,d,e> [...]
    S = <a,b,c,a,d,e,a> [...] 
    --> Now that the third a has been received, delete everything before the second one -> S = <a,d,e,a>

    -->This might lead to incomplete input/output sets though, as it assumes a execution of Fodina that is so regularly, that no possible input/output set (represented by a event trace starting with and ending at a specified event) is skipped. Therefore this procedure would probably only work, if Fodina is executed after every event

    The only other option I see is logging the whole event trace between executions of the fodina algorithm, which then again would lead me to the question why the classic implementation should not be used in cases like this.
    """
    def findPatterns(self, taskParam, dir):
        
        #PS
        extractedPatterns = set()
        #C
        workingSetTasks = set()
        #Pattern Count
        patternCount = {}

        # print('--------------------------------------------------------------')
        # print('Looking at event '+taskParam+', with direction '+dir)
        # print('--------------------------------------------------------------')
        

        #Fill C (FindPatterns Pseudocode Line 7)
        if(dir=='input'):
            # print('Filling WorkingSetTasks')
            for task in self.tasks:
                # print('Checking Edge:')
                # print('('+task+','+taskParam+')')
                if(self.dependencyGraphViz.has_edge(task,taskParam)):
                    workingSetTasks.add(task)

        #Fill C (FindPatterns Pseudocode Line 8)
        elif(dir == 'output'):
            # print('Filling WorkingSetTasks')
            for task in self.tasks:
                # print('Checking Edge:')
                # print('('+taskParam+','+task+')')
                if(self.dependencyGraphViz.has_edge(taskParam,task)):
                    workingSetTasks.add(task)
        
        # print('--------------------------------------')
        # print('WorkingSetPatterns (C) is')
        # print(workingSetTasks)
        # print('--------------------------------------')

        for eventTrace in self.eventLog:
            # print()
            # print('Looking at event trace: ')
            # print(eventTrace)
            # print('-------------------')


            for i in range(0,len(eventTrace),1):
            
                
                if(eventTrace[i] != taskParam):
                    continue

                # print('Now looking at index '+str(i))
                # print()

                #P
                workingSetPatterns = set()

                #c in C
                for currTask in workingSetTasks:

                    # print()
                    # print('WorkingSetPatterns is ')
                    # print(workingSetPatterns)

                    # print()
                    # print('<><><><><><><><><><><><><><><><><><><><><><><><><><><>')
                    # print('Looking at current task '+currTask+' from C')
                    # print('<><><><><><><><><><><><><><><><><><><><><><><><><><><>')
                    # print()

                    if(dir == 'input'):
                        #Set of output tasks for candidate input task (CO)
                        outputTasks = set()

                        for task in self.tasks:
                            if((currTask,task) in self.dependencyGraphViz.edges()):
                                outputTasks.add(task)

                        #FindPatterns Pseudocode Line 15 (cp)
                        cp = -1;
                        #-1 because stop is not included in range
                        for j in range(i-1,-1,-1):
                            if(eventTrace[j] == currTask):
                                cp = j
                                break

                        # print('Nearest Input at index '+str(cp))

                        #Second Part of the condition in FindPatterns Pseudocode Line 21
                        doesKExist = False

                        if(cp != -1 and cp+1 > i-1):
                            #To i instead i-1, because stop is exclusive
                            for k in range(cp+1,i,1):
                                if(eventTrace[k] == taskParam or (eventTrace[k] in outputTasks and (currTask,taskParam) not in self.ldeps)):
                                    doesKExist = True

                        if(cp != -1 and not(doesKExist)):
                            workingSetPatterns.add(currTask)

                    elif(dir == 'output'):
                        #set of input tasks for candidate output task
                        inputTasks = set()

                        for task in self.tasks:
                            if(self.dependencyGraphViz.has_edge(task,currTask)):
                                inputTasks.add(task)

                        # print('CI is:')
                        # print(inputTasks)

                        #FindPatterns Pseudocode Line 20 (cp)
                        cp = -1
                        if(i+1 < len(eventTrace)):
                            for j in range(i+1,len(eventTrace),1):
                                if(eventTrace[j] == currTask):
                                    cp = j 
                                    break

                        # print('CP is '+str(cp))

                        #Second Part of the condition in FindPatterns Pseudocode Line 21
                        doesKExist = False

                        if(cp != -1):
                            #Not i+1, as stop is exclusive 
                            for k in range(cp-1,i,-1):
                                if(eventTrace[k] == taskParam or (eventTrace[k] in inputTasks and (taskParam,currTask) not in self.ldeps)):
                                    doesKExist = True

                        if(cp != -1 and not(doesKExist)):
                            workingSetPatterns.add(currTask)
                            # print()
                            # print('Adding '+currTask+' to P')
                            # print()

                #Add constructed pattern to PS and increment pattern count (or set to 0)
                if(len(workingSetPatterns) > 0):
                    extractedPatterns.add(frozenset(workingSetPatterns))

                    if(frozenset(workingSetPatterns) in patternCount):
                        patternCount[frozenset(workingSetPatterns)] +=1
                    else:
                        patternCount[frozenset(workingSetPatterns)] = 0

        # print('Extracted Patterns')
        # print(extractedPatterns)
        # print('--------------------------------------------------------------')
        # print()

        return self.filterPatterns(taskParam,extractedPatterns,workingSetTasks, patternCount)

    def filterPatterns(self, task, extractedPatterns, connectedTasks, patternCount):

        retainedPatterns = set()

        if(len(extractedPatterns) > 0):

            #Pseudocode FilterPatterns (Line 29)
            tr = 0
            for pattern in extractedPatterns:
                tr += (patternCount[pattern]) / (self.taskCount[task] * len(extractedPatterns))

            #Pseudocode FilterPatterns (Line 30-31)
            if(self.configuration.tpat <= 0):
                tr = tr + self.configuration.tpat*tr
            else:
                tr = tr + self.configuration.tpat*(1-tr)

            #Pseudocode FilterPatterns (Line 32-33)
            for pattern in extractedPatterns:
                if((patternCount[pattern]) / (self.taskCount[task]) >= tr):
                    retainedPatterns.add(pattern)

        #Pseudocode FilterPatterns (Line 34-35)
        for task in connectedTasks:
            taskContainedInPattern = False

            for pattern in extractedPatterns:
                if(task in pattern):
                    taskContainedInPattern = True

            if(not(taskContainedInPattern)):
                patternToAdd = set()
                patternToAdd.add(task)
                retainedPatterns.add(frozenset(patternToAdd))

        return retainedPatterns

    def constructPetriNet(self):
        visited=[]
        stack=[]
        nodesAlreadyInPetriNet = []

        stack.append(self.startTask)

        # print()
        # print('--------------------------')

        #Check via hash, runtime is O(n)
        while(Counter(visited) != Counter(self.tasks)):

            #In case the stack is empty, but not all nodes have been visited, it means, that there are unconnected parts of the graph
            #This case can only occur if the ConnectNet option is not set
            if(len(stack) == 0):
                stack.append(list(set(self.tasks) - set(visited)).pop(0))

            nodeCurr = stack.pop(0)
            visited.append(nodeCurr)

            #Add neigbors (according to input/output bindings) that were not seen already 
            #Note that a new neighbor that has not already been seen can only be taken from an input binding, if it is a node that is not reachable from start
            #i.e. that can only occur when the ConnectNet option is not set

            for inputBindingOfCurr in self.inputBindings[nodeCurr]:
                for nodeInputBinding in inputBindingOfCurr:
                    if(nodeInputBinding not in visited and nodeInputBinding not in stack):
                        stack.append(nodeInputBinding)

            for outputBindingCurr in self.outputBindings[nodeCurr]:
                for nodeOutputBinding in outputBindingCurr:
                    if(nodeOutputBinding not in visited and nodeOutputBinding not in stack):
                        stack.append(nodeOutputBinding)


            # print()
            # print('_---------------_')
            # print('Looking at '+nodeCurr)
            # print()
            # print('Output Binding is ')
            # print(self.outputBindings[nodeCurr])

            if(not(self.petriNet.has_node(nodeCurr))):
                # print()
                # print('Adding Node '+nodeCurr)
                self.petriNet.add_node(nodeCurr, eventInfo=computeEventInfo(nodeCurr, self.eventTimes, self.mapActivityToLabel))
                nodesAlreadyInPetriNet.append(nodeCurr)

            for outputBindingCurr in self.outputBindings[nodeCurr]:
                
                #Check InputBindings of the node where transition is supposed to go to. 
                #If there is a binding with multiple elements, in which the current node occurs, that means, 
                #that more than one node will use the transition to get to the desired state
                #TODO: Intuitively it makes only sense for our case if current OutputBindings size is 1 -> verify

                sourceForTransitionLabel = ""

                if(len(outputBindingCurr) == 1):
                    #Iterate over inputBindings of the outputBinding that is currently looked at
                    for inputBinding in self.inputBindings[list(outputBindingCurr)[0]]:
                        # print('Input Binding for currently regarded output binding '+str(outputBindingCurr))
                        # print(inputBinding)

                        if(nodeCurr in inputBinding):
                            sourceForTransitionLabel = '{'+','.join(inputBinding)+'}'
                
                
                if(sourceForTransitionLabel != ""):
                    transitionLabel = str(sourceForTransitionLabel+'_to_{'+','.join(outputBindingCurr)+'}')
                else:
                    transitionLabel = str('{'+nodeCurr+'}_to_{'+','.join(outputBindingCurr)+'}')

                # print()
                # print('Transition Label: '+transitionLabel)

                # print()
                # print('Adding Node '+transitionLabel)
                self.petriNet.add_node(transitionLabel, shape="box", label="", width=0.4, height=0.3)
                #Incoming edge to transition
                # print()
                # print('Adding Edge from '+nodeCurr+' to '+transitionLabel)
                self.petriNet.add_edge(nodeCurr, transitionLabel)

                #Outgoing edges from transition
                for nodeOutputBinding in outputBindingCurr:
                    # print()
                    # print('Current Element from Output Bindings of '+nodeCurr+' is '+nodeOutputBinding)
                    
                    if(not(self.petriNet.has_node(nodeOutputBinding))):
                        # print()
                        # print('Adding Node '+nodeOutputBinding)
                        self.petriNet.add_node(nodeOutputBinding, eventInfo=computeEventInfo(nodeOutputBinding, self.eventTimes, self.mapActivityToLabel))
                        nodesAlreadyInPetriNet.append(nodeOutputBinding)
                    # print()
                    # print('Adding Edge from '+transitionLabel+' to '+nodeOutputBinding)
                    self.petriNet.add_edge(transitionLabel, nodeOutputBinding)

        self.petriNet.layout()
        self.petriNet.draw('results/petriNetTest.png')

        self.petriNet.layout(prog="circo")
        self.petriNet.draw('results/petriNetTest2.png')

    

        
class FodinaClassic: 

    def __init__(self, paramEventLog, paramConfig, paramEventTimes, paramMapActivityToLabel):
        self.eventLog = paramEventLog
        self.configuration = paramConfig
        self.mapDuplicateTasks = {}
        self.directSuccession = {}
        self.repetitionCount = {}
        self.indirectSuccessionCount = {}
        self.dependencyGraphViz = pgv.AGraph(directed=True) 

        self.tasks = []
        self.taskCount = {}
        self.startTask = ""
        self.endTask = ""
        self.ldeps = set()
        self.inputBindings = {}
        self.outputBindings = {}
        self.petriNet = pgv.AGraph(directed=True)

        self.eventTimes = paramEventTimes
        self.mapActivityToLabel = paramMapActivityToLabel

    def runFodinaClassic(self):
        #Step 1
        self.constructTaskLog(self.configuration.mineDuplicates)

        #Step 2
        self.deriveBasicRelations()

        #Step 3
        self.dependencyGraphViz = constructBasicDependencyGraph(self.tasks, self.dependencyGraphViz, self.directSuccession, self.repetitionCount, self.configuration.td, self.configuration.tl1l, self.configuration.tl2l, self.configuration.noL2LWithL1l)

        #Step 4
        self.setStartAndEndTask()

        #Step 5
        if(self.configuration.noBinaryConflicts):
            self.dependencyGraphViz = resolveBinaryConflicts(self.dependencyGraphViz, self.repetitionCount, self.tasks)

        #Step 6
        if(self.configuration.connectNet and len(self.dependencyGraphViz.nodes()) > 0):
            self.dependencyGraphViz = assureReachability(self.directSuccession, self.startTask, self.endTask, self.dependencyGraphViz, self.tasks)

        #Step 7
        self.mineLongDependencies()

        #Step 8 (mine Split and Join Semantics)
        for task in self.tasks:
            inputBindingsCurr = self.findPatterns(task, 'input')
            outputBindingsCurr = self.findPatterns(task, 'output')

            self.inputBindings[task] = inputBindingsCurr
            self.outputBindings[task] = outputBindingsCurr

        #Has to be done, enriches the graph with position info etc, so that the GraphParser can handle the transition for it to be shown in the UI
        self.dependencyGraphViz.layout()
        self.dependencyGraphViz.draw('results/graphTest.png')

        self.dependencyGraphViz.layout(prog="circo")
        self.dependencyGraphViz.draw('results/graphTest2.png')


        #From Input-/Output-Bindings construct Petri Net
        self.constructPetriNet()

    

    #TODO: Duplicate Tasks zurückmappen auf ursprüngliches label -> irrelevant für Stream
    """
    Computation of the actual petri net on the basis of the input/output bindings.
    Furthermore the petri net is constructed as a graph, where a differentiation between places and transitions is easily to be seen, so that the client can parse it better.

    The resulting petri net therefore has edges of the form a -> {a_to_{b,c}}, {b,c}_to_b -> b, {b,c}_to_c representing there is a (AND) transition from place a to places b and c
    """
    def constructPetriNet(self):
        visited=[]
        stack=[]
        nodesAlreadyInPetriNet = []

        stack.append(self.startTask)

        #Check via hash, runtime is O(n)
        while(Counter(visited) != Counter(self.tasks)):

            #In case the stack is empty, but not all nodes have been visited, it means, that there are unconnected parts of the graph
            #This case can only occur if the ConnectNet option is not set
            if(len(stack) == 0):
                stack.append(list(set(self.tasks) - set(visited)).pop(0))

            nodeCurr = stack.pop(0)
            visited.append(nodeCurr)

            #Add neigbors (according to input/output bindings) that were not seen already 
            #Note that a new neighbor that has not already been seen can only be taken from an input binding, if it is a node that is not reachable from start
            #i.e. that can only occur when the ConnectNet option is not set

            for inputBindingOfCurr in self.inputBindings[nodeCurr]:
                for nodeInputBinding in inputBindingOfCurr:
                    if(nodeInputBinding not in visited and nodeInputBinding not in stack):
                        stack.append(nodeInputBinding)

            for outputBindingCurr in self.outputBindings[nodeCurr]:
                for nodeOutputBinding in outputBindingCurr:
                    if(nodeOutputBinding not in visited and nodeOutputBinding not in stack):
                        stack.append(nodeOutputBinding)

            if(not(self.petriNet.has_node(nodeCurr))):

                self.petriNet.add_node(nodeCurr, eventInfo=computeEventInfo(nodeCurr, self.eventTimes, self.mapActivityToLabel))
                nodesAlreadyInPetriNet.append(nodeCurr)

            for outputBindingCurr in self.outputBindings[nodeCurr]:
                
                #Check InputBindings of the node where transition is supposed to go to. 
                #If there is a binding with multiple elements, in which the current node occurs, that means, 
                #that more than one node will use the transition to get to the desired state
                #TODO: Intuitively it makes only sense for our case if current OutputBindings size is 1 -> verify

                sourceForTransitionLabel = ""

                if(len(outputBindingCurr) == 1):
                    #Iterate over inputBindings of the outputBinding that is currently looked at
                    for inputBinding in self.inputBindings[list(outputBindingCurr)[0]]:

                        if(nodeCurr in inputBinding):
                            sourceForTransitionLabel = '{'+','.join(inputBinding)+'}'
                
                
                if(sourceForTransitionLabel != ""):
                    transitionLabel = str(sourceForTransitionLabel+'_to_{'+','.join(outputBindingCurr)+'}')
                else:
                    transitionLabel = str('{'+nodeCurr+'}_to_{'+','.join(outputBindingCurr)+'}')

                self.petriNet.add_node(transitionLabel, shape="box", label="", width=0.4, height=0.3)
                #Incoming edge to transition
                self.petriNet.add_edge(nodeCurr, transitionLabel)

                #Outgoing edges from transition
                for nodeOutputBinding in outputBindingCurr:

                    if(not(self.petriNet.has_node(nodeOutputBinding))):

                        self.petriNet.add_node(nodeOutputBinding, eventInfo=computeEventInfo(nodeOutputBinding, self.eventTimes, self.mapActivityToLabel))
                        nodesAlreadyInPetriNet.append(nodeOutputBinding)

                    self.petriNet.add_edge(transitionLabel, nodeOutputBinding)

        #Has to be done, enriches the graph with position info etc, so that the GraphParser can handle the transition for it to be shown in the UI
        #Depending on what layout was chosen last, the graph will appear differently. If you want to fiddle around with that, you can choose between the following options for prog: dot, neato, fdp, sfdp, circo, twopi, nop, nop2, osage, patchwork (https://graphviz.org/docs/layouts/)
        self.petriNet.layout()
        self.petriNet.draw('results/petriNetTest.png')

        self.petriNet.layout(prog="circo")
        self.petriNet.draw('results/petriNetTest2.png')

    """
    Step 8 of Fodina algorithm: Mine Split and Join Semantics
    This is done by computing the input and output bindings of all the tasks in the event traces by counting the number of times patterns (subset of input/output tasks) is seen after the occurence of the task.

    With the bindings found, for a task having multiple incoming/outgoing edges in the dependency graph it can then be derived if it is a AND or XOR connection
    """
    def findPatterns(self, taskParam, dir):
        
        #PS
        extractedPatterns = set()
        #C
        workingSetTasks = set()
        #Pattern Count
        patternCount = {}

        #Fill C (FindPatterns Pseudocode Line 7)
        if(dir=='input'):
            for task in self.tasks:

                if(self.dependencyGraphViz.has_edge(task,taskParam)):
                    workingSetTasks.add(task)

        #Fill C (FindPatterns Pseudocode Line 8)
        elif(dir == 'output'):
            for task in self.tasks:

                if(self.dependencyGraphViz.has_edge(taskParam,task)):
                    workingSetTasks.add(task)

        for eventTrace in self.eventLog:

            for i in range(0,len(eventTrace),1):
                
                if(eventTrace[i] != taskParam):
                    continue

                #P
                workingSetPatterns = set()

                #c in C
                for currTask in workingSetTasks:

                    if(dir == 'input'):
                        #Set of output tasks for candidate input task (CO)
                        outputTasks = set()

                        for task in self.tasks:
                            if((currTask,task) in self.dependencyGraphViz.edges()):
                                outputTasks.add(task)

                        #FindPatterns Pseudocode Line 15 (cp)
                        cp = -1;
                        #-1 because stop is not included in range
                        for j in range(i-1,-1,-1):
                            if(eventTrace[j] == currTask):
                                cp = j
                                break

                        #Second Part of the condition in FindPatterns Pseudocode Line 21
                        doesKExist = False

                        if(cp != -1 and cp+1 > i-1):
                            #To i instead i-1, because stop is exclusive
                            for k in range(cp+1,i,1):
                                if(eventTrace[k] == taskParam or (eventTrace[k] in outputTasks and (currTask,taskParam) not in self.ldeps)):
                                    doesKExist = True

                        if(cp != -1 and not(doesKExist)):
                            workingSetPatterns.add(currTask)

                    elif(dir == 'output'):
                        #set of input tasks for candidate output task
                        inputTasks = set()

                        for task in self.tasks:
                            if(self.dependencyGraphViz.has_edge(task,currTask)):
                                inputTasks.add(task)

                        #FindPatterns Pseudocode Line 20 (cp)
                        cp = -1
                        if(i+1 < len(eventTrace)):
                            for j in range(i+1,len(eventTrace),1):
                                if(eventTrace[j] == currTask):
                                    cp = j 
                                    break

                      #print('CP is '+str(cp))

                        #Second Part of the condition in FindPatterns Pseudocode Line 21
                        doesKExist = False

                        if(cp != -1):
                            #Not i+1, as stop is exclusive 
                            for k in range(cp-1,i,-1):
                                if(eventTrace[k] == taskParam or (eventTrace[k] in inputTasks and (taskParam,currTask) not in self.ldeps)):
                                    doesKExist = True

                        if(cp != -1 and not(doesKExist)):
                            workingSetPatterns.add(currTask)

                #Add constructed pattern to PS and increment pattern count (or set to 0)
                if(len(workingSetPatterns) > 0):
                    extractedPatterns.add(frozenset(workingSetPatterns))

                    if(frozenset(workingSetPatterns) in patternCount):
                        patternCount[frozenset(workingSetPatterns)] +=1
                    else:
                        patternCount[frozenset(workingSetPatterns)] = 0

        return self.filterPatterns(taskParam,extractedPatterns,workingSetTasks, patternCount)

    def filterPatterns(self, task, extractedPatterns, connectedTasks, patternCount):

        retainedPatterns = set()

        if(len(extractedPatterns) > 0):

            #Pseudocode FilterPatterns (Line 29)
            tr = 0
            for pattern in extractedPatterns:
                tr += (patternCount[pattern]) / (self.taskCount[task] * len(extractedPatterns))

            #Pseudocode FilterPatterns (Line 30-31)
            if(self.configuration.tpat <= 0):
                tr = tr + self.configuration.tpat*tr
            else:
                tr = tr + self.configuration.tpat*(1-tr)

            #Pseudocode FilterPatterns (Line 32-33)
            for pattern in extractedPatterns:
                if((patternCount[pattern]) / (self.taskCount[task]) >= tr):
                    retainedPatterns.add(pattern)

        #Pseudocode FilterPatterns (Line 34-35)
        for task in connectedTasks:
            taskContainedInPattern = False

            for pattern in extractedPatterns:
                if(task in pattern):
                    taskContainedInPattern = True

            if(not(taskContainedInPattern)):
                patternToAdd = set()
                patternToAdd.add(task)
                retainedPatterns.add(frozenset(patternToAdd))

        return retainedPatterns

    """
    (Optional) Step 7 of Fodina: Mine Long Dependencies
    Adds long distance dependencies for task pairs (a,b) where a specific threshold is met and for which there exist a path from start to end without visiting either the start or end task and a path from a to b without visiting end
    """
    def mineLongDependencies(self):
        if(self.configuration.mineLongDependencies):

            for a in self.tasks:
                for b in self.tasks:
                    if(a == b):
                        continue

                    valueToCheck = (2*self.indirectSuccessionCount.get((a,b),0))/(self.taskCount[a] + self.taskCount[b] + 1) - (2*abs(self.taskCount[a]-self.taskCount[b])) / (self.taskCount[a] + self.taskCount[b] + 1)

                    if(valueToCheck >= self.configuration.tld):

                        if(self.pathExistsFromToWithoutVisiting(self.startTask,self.endTask,a) and self.pathExistsFromToWithoutVisiting(self.startTask,self.endTask,b) and self.pathExistsFromToWithoutVisiting(a,self.endTask,b)):
                            self.dependencyGraphViz.add_edge(a,b)
                            self.ldeps.add((a,b))
        return


    def pathExistsFromToWithoutVisiting(self,start,end,without):
        visited=[]
        stack=[]

        stack.append(start)

        while(len(stack) > 0):  
            currNode = stack.pop(0)

            #If end node is found, algorithm terminates
            if(currNode == end):
                return True

            visited.append(currNode)
            
            for currNeighbor in self.dependencyGraphViz.successors(currNode):
                if(currNeighbor not in visited and currNeighbor != without):
                    stack.append(currNeighbor)

        return False

    """
    Step 4 of Fodina: Set start and end task
    For the classical Fodina this is done by choosing the last elements of the event traces and selecting the maximum for the first and last elements in the event traces 
    """
    def setStartAndEndTask(self):

        firstElements = [eventTrace[0] for eventTrace in self.eventLog]
        firstCount = Counter(firstElements)

        self.startTask = max(firstCount, key=firstCount.get)

        lastElements = [eventTrace[-1] for eventTrace in self.eventLog]
        lastCount = Counter(lastElements)

        self.endTask = max(lastCount, key=lastCount.get)

        #Throw out edges (x,start) and (end, x)
        edgesToRemove = []

        for edge in self.dependencyGraphViz.edges():
            source = edge[0]
            sink = edge[1]

            if(source == self.endTask or sink == self.startTask):
                edgesToRemove.append(edge)

        for edgeToRemove in edgesToRemove:
            self.dependencyGraphViz.remove_edge(edgeToRemove)
        

    """
    (Optional) Step 1 of Fodina: Constructs the TaskLog from the EventLog. This is only necessary when the mineDuplicates option is set.

    Step 1: Event Log is collapsed; allow to “collapse” repeated tasks during the derivation of duplicates 
    -> the event log is copied, so that we do not need to place a dummy but can delete the consecutive duplicates. Once the contexts are derived, the copy is not needed anymore

    Step 2: Create Contexts from collapsed Event Log

    Step 3: Create Grouped Contexts from Contexts 

    The distinction between duplicate tasks is done by substituting a duplicate task with a new one with the same name and an additional id, starting at 1337,
    because the possibility of an item named a_1 is higher than a_1337

    TODO: Threshold T_dup
    TODO: Think about how to handle the fact that simple ORs might be considered duplicate events

    -->Not needed for either the Classic Fodina Implementation, nor the Stream-Based variant. Also a bit buggy still 

    """
    def constructTaskLog(self, mineDuplicates):

        if(mineDuplicates):
            #Step 1: Collapse
            collapsedEventLog = []

            for eventTrace in self.eventLog:
                lastSeen = '-'
                collapsedTrace = []

                for event in eventTrace:
                    if(event != lastSeen):
                        collapsedTrace.append(event)
                    lastSeen = event
                collapsedEventLog.append(collapsedTrace)

            # print(collapsedEventLog)

            #Step 2: Contexts
            mapEventToContext = {}

            for eventTrace in collapsedEventLog:
                for i in range(0, len(eventTrace),1):
                    event = eventTrace[i]

                    #TODO: Hässlich, neu machen!

                    #If event has no key in the map yet, add it
                    if(event != 'start' and event !='end' and event not in mapEventToContext):
                        mapEventToContext[event] = set()

                    if(i > 0 and i < len(eventTrace) and event != 'start' and event !='end'):
                        mapEventToContext[event].add((eventTrace[i-1], eventTrace[i], eventTrace[i+1]))

            #Step 3: Grouped Contexts

            mapEventToGroupedContext = {}

            for event in mapEventToContext:
                groupedContexts = []
                # print('Starting for '+event+' --------------------------------------------------------------------------------------')

                for currContext in mapEventToContext[event]:
                    x, y, z = currContext
                    conflictSets = []

                    # Iterate working set of grouped contexts
                    for existingSet in groupedContexts:
                        # Check for conflict with curr element
                        hasConflict = any(j == y and (x == i or z == k) for (i, j, k) in existingSet)
                        
                        if hasConflict:
                            conflictSets.append(existingSet)

                    # No Conflict -> new grouped context
                    if not conflictSets:
                        #Merge with existing one, if overlapping one is found -> TODO: is it needed tho?
                        merged = False

                        for existingSet in groupedContexts:
                            if any((x1 == x or z1 == z) for (x1, _, z1) in existingSet):
                                existingSet.add((x, y, z))
                                merged = True
                                break

                        if not merged:
                            new_set = {(x, y, z)}
                            groupedContexts.append(new_set)
                    else:
                        # Conflict -> combine with conflicting one
                        combinedSet = {(x, y, z) for s in conflictSets for (x, y, z) in s}
                        combinedSet.add((x, y, z))

                        groupedContexts = [s for s in groupedContexts if s not in conflictSets]
                        groupedContexts.append(combinedSet)

                # print(groupedContexts)
                mapEventToGroupedContext[event] = groupedContexts

            #Rename elements, that were identified as duplicates 
            for eventToReplace in mapEventToGroupedContext:
                
                dupId = 1337

                if(len(mapEventToGroupedContext) ==1):
                    continue

                sequencesToReplace = mapEventToGroupedContext[eventToReplace]

                #First one will keep its original name
                for i in range(1,len(sequencesToReplace),1):

                    for currTuple in sequencesToReplace[i]:

                        #Iterate over event log
                        for eventTrace in self.eventLog:
                            for i in range(1, len(eventTrace)-1,1):

                                #TODO: Tasks that have a self-loop
                                if(eventTrace[i-1] == currTuple[0] and eventTrace[i] == currTuple[1]):
                                    # hit = False

                                    """
                                    While the next element is the middle-element of our currTuple we need to check for the next to see if eventually the next one is identical
                                    If that is the case, then we are looking at a self loop here which was ignored in the creation of the sequences to replace, as it worked with 
                                    the collapsed eventLog. However, all of these elements have to be substituted
                                    """
                                    j = i+1
                                    while(j<len(eventTrace) and eventTrace[j] == currTuple[1]):
                                        j+=1

                                    if(eventTrace[j] == currTuple[2]):
                                        newName = eventTrace[i]+str(dupId)
                                        self.mapDuplicateTasks[newName] = eventTrace[i]

                                        while(i<j):
                                            eventTrace[i] = eventTrace[i]+str('_')+str(dupId)
                                            i+=1

                                

                    dupId +=1

    
    """
    Step 2 of Fodina: Does the counting for the basic relations: directSuccession, repetitionCount and indirectSuccessionCount

    DirectSuccession:
        the direct succession count between a and b (the number of times that a is directly followed by b)

    RepetitionCount: 
        the repetition count between a and b (the number of times that a is directly followed by b and b again followed by a)
    
    IndirectSuccession Count: 
        the indirect succession count between a and b (the number of times that a is eventually followed by b, but before the next appearance of a or b)
    """
    def deriveBasicRelations(self):

        #Store events to have a overview of all and count them
        for eventTrace in self.eventLog:
            for event in eventTrace:

                if event not in self.tasks:
                    self.tasks.append(event)
                    self.taskCount[event] = 1
                else:
                    self.taskCount[event] += 1    
        
        for eventTrace in self.eventLog:
            i=0
            #-2 because like this we can do directSuccession and Repetition Count in one loop -> afterwards, the direct succession has to be checked outside the loop once though
            while i < len(eventTrace)-2:
                if (eventTrace[i],eventTrace[i+1]) in self.directSuccession:
                    self.directSuccession[(eventTrace[i],eventTrace[i+1])] +=1
                else:
                    self.directSuccession[(eventTrace[i],eventTrace[i+1])] = 1

                if(eventTrace[i+2] == eventTrace[i]):
                    if (eventTrace[i],eventTrace[i+1]) in self.repetitionCount:
                        self.repetitionCount[(eventTrace[i],eventTrace[i+1])] +=1
                    else:
                        self.repetitionCount[(eventTrace[i],eventTrace[i+1])] = 1

                # print(eventTrace[i]+','+eventTrace[i+1])
                i+=1

            #Said addtional check
            if(len(eventTrace) > 1):
                if (eventTrace[i],eventTrace[i+1]) in self.directSuccession:
                    self.directSuccession[(eventTrace[i],eventTrace[i+1])] += 1
                else:
                    self.directSuccession[(eventTrace[i],eventTrace[i+1])] = 1

        #Indirect Succession Count

        for eventTrace in self.eventLog:
            for i in range(0,len(eventTrace),1):
                for j in range(i+1,len(eventTrace),1):

                    #If the same element is found, the function has to go to the next iteration for i (see definition (comment on method))
                    if(eventTrace[i] == eventTrace[j]):
                        break
                    else:
                        if (eventTrace[i],eventTrace[j]) in self.indirectSuccessionCount:
                            self.indirectSuccessionCount[(eventTrace[i],eventTrace[j])] += 1
                        else:
                            self.indirectSuccessionCount[(eventTrace[i],eventTrace[j])] = 1   

"""
(Optional) Step 6 of Fodina Algorithm: Connect Net.
Computes the nodes that are not reachable from start or the ones that do not reach the end and connects them by choosing the best candidate
"""
def assureReachability(directSuccession, startTask, endTask, dependencyGraphViz, tasks):

    #Find nodes that are not reachable from start or that do not reach end
    nodesReachableFromStart = depthFirstSearch(startTask, False, dependencyGraphViz)
    nodesThatReachEnd = depthFirstSearch(endTask, True, dependencyGraphViz)

    notConnectedToStart = list(set(dependencyGraphViz.nodes()) - set(nodesReachableFromStart))
    notConnectedToEnd = list(set(dependencyGraphViz.nodes()) - set(nodesThatReachEnd))

    hasUnconnectedTasks = len(notConnectedToStart) > 0 and len(notConnectedToEnd) > 0

    while(hasUnconnectedTasks):

        #Pseudocode Line 22
        argmax = -1
        candidate = tuple()
        for unconnectedToStart in notConnectedToStart:
            for task in tasks:

                candidateEdge = (task, unconnectedToStart)

                if(candidateEdge in dependencyGraphViz.edges() or unconnectedToStart == startTask or task == endTask):
                    continue
                valueCandidate = (directSuccession.get(candidateEdge,0)) / (directSuccession.get(candidateEdge,0) + directSuccession.get(tuple(reversed(candidateEdge)),0) +1)

                if(valueCandidate > argmax):
                    argmax = valueCandidate
                    candidate = candidateEdge
                
        dependencyGraphViz.add_edge(candidate[0],candidate[1])

        #Pseudocode Line 25
        argmax = -1
        candidate = tuple()
        for unconnectedToEnd in notConnectedToEnd:
            for task in tasks:

                candidateEdge = (unconnectedToEnd, task)

                if(candidateEdge in dependencyGraphViz.edges() or unconnectedToStart == startTask or task == endTask):
                    continue
                valueCandidate = (directSuccession.get(candidateEdge,0)) / (directSuccession.get(candidateEdge,0) + directSuccession.get(tuple(reversed(candidateEdge)),0) +1)

                if(valueCandidate > argmax):
                    argmax = valueCandidate
                    candidate = candidateEdge
                
        dependencyGraphViz.add_edge(candidate[0],candidate[1])

        nodesReachableFromStart = depthFirstSearch(startTask, False, dependencyGraphViz)
        nodesThatReachEnd = depthFirstSearch(endTask, True, dependencyGraphViz)

        notConnectedToStart = list(set(dependencyGraphViz.nodes()) - set(nodesReachableFromStart))
        notConnectedToEnd = list(set(dependencyGraphViz.nodes()) - set(nodesThatReachEnd))

        hasUnconnectedTasks = len(notConnectedToStart) > 0 and len(notConnectedToEnd) > 0

    return dependencyGraphViz

def depthFirstSearch(node, backwards, dependencyGraphViz):
    visited=[]
    stack=[]

    stack.append(node)

    while(len(stack) > 0):  
        currNode = stack.pop(0)
        visited.append(currNode)
        
        if(backwards):
            for currNeighbor in dependencyGraphViz.predecessors(currNode):
                if(currNeighbor not in visited):
                    stack.append(currNeighbor)
        else:
            for currNeighbor in dependencyGraphViz.successors(currNode):
                if(currNeighbor not in visited):
                    stack.append(currNeighbor)
    return visited

"""
(Optional) Step 5 of the Fodina Algorithm: Resolves Binary Conflicts
Eliminates loops of length 2 from the dependency graph and updates connections accordingly
"""
def resolveBinaryConflicts(dependencyGraphViz, repetitionCount, tasks):
    
    #Store every edge that was already seen, so that the function is not executed for (a,b) and (b,a) and later for (b,a) and (a,b) as they are the same
    alreadySeen = set()

    #Pseudocode Line 11
    for edge in dependencyGraphViz.edges():

        source = edge[0]
        sink = edge[1]

        if(source==sink or (sink,source) in alreadySeen):
            continue

        if(dependencyGraphViz.has_edge(sink,source)):
            #Pseudocode Line 12
            dependencyGraphViz.remove_edge(source,sink)
            dependencyGraphViz.remove_edge(sink,source)

            #Pseudocode Line 13
            if(repetitionCount.get((source, sink),0) > 0):
                dependencyGraphViz.add_edge(source,source)
                
            #Pseudocode Line 14
            if(repetitionCount.get((sink, source),0) > 0):
                dependencyGraphViz.add_edge(sink,sink)

            #Pseudocode Line 15
            for task in tasks:
                if(task == source or task == sink):
                    continue
                        
                #Pseudocode Line 16
                if(dependencyGraphViz.has_edge(task,source) or dependencyGraphViz.has_edge(task, sink)):
                    dependencyGraphViz.add_edge(task, source)
                    dependencyGraphViz.add_edge(task, sink)

                #Pseudocode Line 17
                if(dependencyGraphViz.has_edge(source,task) or dependencyGraphViz.has_edge(sink, task)):
                    dependencyGraphViz.add_edge(source, task)
                    dependencyGraphViz.add_edge(sink, task)

        alreadySeen.add((source,sink))

    return dependencyGraphViz

"""
Step 3 of the Fodina Algorithm: Using the counts direct succession and repetition count, a basic dependency graph is computed 
depicting the directly-follows-abstraction for the received events / the event traces
"""
def constructBasicDependencyGraph(tasks, dependencyGraphViz, directSuccession, repetitionCount, td, tl1l, tl2l, noL2LWithL1l):

    for task1 in tasks:
        for task2 in tasks:

            value1 = directSuccession.get((task1, task2), 0)
            value2 = directSuccession.get((task2, task1), 0)

            #Pseudocode Line 2
            if task1 == task2 :

                if((task1,task2) in directSuccession):
                    valueSelfLoop = (directSuccession[(task1,task2)]) / (directSuccession[(task1,task2)] + 1)

                    if(valueSelfLoop >= tl1l):
                        dependencyGraphViz.add_edge(task1,task2)

            #Pseudocode Line 3
            valueDirectSuccession = (value1) / (value1 + value2 + 1)

            if(valueDirectSuccession >= td):
                dependencyGraphViz.add_edge(task1,task2)

            #Pseudocode Line 4
            value1 = repetitionCount.get((task1, task2), 0)
            value2 = repetitionCount.get((task2, task1), 0)
            valueRepetitionCount = (value1 + value2) / (value1 + value2 + 1)

            dependencyGraphEdges = dependencyGraphViz.edges()

            if(valueRepetitionCount >= tl2l and (not(noL2LWithL1l) or (task1,task1) not in dependencyGraphEdges or (task2,task2) not in dependencyGraphEdges)):
                dependencyGraphViz.add_edge(task1,task2)
                dependencyGraphViz.add_edge(task2,task1)
   
    return dependencyGraphViz

"""
Enriches the nodes with the event info, meaning the different timestamps (earliest, latest, average, median) and the label 
"""
def computeEventInfo(node, eventTimes, mapActivityToLabel):
    rst = {}
    dateFormatRst = "%d.%m.%Y %H:%M:%S"
    dateFormat = '%Y-%m-%dT%H:%M:%S.%f%z'

    eventTimesForNode = eventTimes[node]

    rst['firstEvent'] = datetime.strftime(datetime.strptime(eventTimesForNode[0], dateFormat),dateFormatRst)
    rst['lastEvent'] = datetime.strftime(datetime.strptime(eventTimesForNode[-1], dateFormat),dateFormatRst)

    #Average
    sumTimestamps = 0

    for date in eventTimesForNode:
        sumTimestamps += datetime.strptime(date,dateFormat).timestamp()
        

    avgTimestamp = sumTimestamps / len(eventTimesForNode)
    avgDate = datetime.utcfromtimestamp(avgTimestamp)

    #UTCFromTimeStamp is one hour off to our time, therefore add one hour
    avgDate  += timedelta(hours=1)
    avgDateStr = avgDate.strftime(dateFormatRst)

    rst['averageEvent'] = avgDateStr

    #Median
    length = len(eventTimesForNode)
    if(length % 2 == 0):
        lowerMiddle = eventTimesForNode[length // 2 -1]
        upperMiddle = eventTimesForNode[length // 2]

        sumTimestamps = datetime.strptime(lowerMiddle,dateFormat).timestamp() + datetime.strptime(upperMiddle,dateFormat).timestamp()

        medianTimestamp = sumTimestamps / 2
        medianDate = datetime.utcfromtimestamp(medianTimestamp)

        #UTCFromTimeStamp is one hour off to our time, therefore add one hour
        medianDate  += timedelta(hours=1)
        medianDateStr = medianDate.strftime(dateFormatRst)

        rst['medianEvent'] = medianDateStr
    else:
        rst['medianEvent'] = datetime.strftime(datetime.strptime(eventTimesForNode[length // 2], dateFormat), dateFormatRst)

    #Add Label of the activity
    rst['activityLabel'] = mapActivityToLabel[node]

    return rst
