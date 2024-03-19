<h1>Installing the project</h1>
Once you have cloned the repository:
<ul>
<li>Navigate to the client directory and run: npm install</li>
<li>Navigate to the server directory and run: pip install -r requirements.txt</li>
</ul>

<h1>Starting the project</h1>

<h3>To run server enter</h3>

source venv/bin/activate
python3 app.py

Before the application can run properly, the port forwarding to localhost:8082 needs to be instantiated.

This is done by running ssh (name)@lehre.bpm.in.tum.de -R 10122:localhost:8082 in a terminal

If there are issues with the permission being denied, that can be fixed by doing the following steps:

<ul>
<li>Ensure the ssh agent is running: eval $(ssh-agent) </li>
<li>add the private key to the servers public key to the ssh-agent: ssh-add ~/.ssh/path/to/key (in my instance ssh-add ~/.ssh/prak_key) </li>
</ul>

<h3>To run client enter</h3>

npm install (if not done before)
npm run dev

<h1>Structure of the Project<h1>

<h3>Client</h3>

<ul>
<li>index.tsx: Holds the structure of the webapp (navigation, etc) and the websockets that are used</li>
<li>MainPage.tsx: Holds the webpage, written in React (Next).js</li>
<li>MainPage.css: The styling for the webpage</li>
<li>Graph.js: The graphical representation of the graphs, using react-cytoscapejs</li>
<li>GraphParser.js: Parses the string-representation of the GraphViz-Component that was generated and sent from the backend</li>
</ul>

<h3>Server</h3>

<ul>
<li>app.py: Entry Point for the server. Handles all communication and starting of the Fodina runs. Also manages receiving of the events via the stream</li>
<li>fodina.py: Holds the Fodina algorithm, the classic version as well as the stream-based one. Is called from app.py</li>
<li>abstractRepresentation.py: The abstract representation, based on the event stream-based process discovery paper. An instance is hold and maintained in app.py</li>
<li>configuration.py: A class, which represents all the configurable options in the frontend and manages the event flow during the Fodina execution</li>
<li>Directory resources/models_xml: Holds the xml models, that can be used for the generation. Here other xml models can be added to be tried as well <b>not tested</b></li>
</ul>

<br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/><br/>
<b> In the midst of chaos, there is also Opportunity</b>
<br/>
<b>-Sun Tzu</b>
