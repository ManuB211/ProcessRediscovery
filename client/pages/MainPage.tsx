import React, { useState, useRef } from "react";
import SettingsIcon from "@mui/icons-material/Settings";
import AnalyticsIcon from "@mui/icons-material/Analytics";
import CameraAltIcon from "@mui/icons-material/CameraAlt";
import InfoIcon from "@mui/icons-material/Info";
// import DeleteIcon from "@mui/icons-material/Delete";
import Checkbox from "@mui/material/Checkbox";
import Button from "@mui/material/Button";
// import List from "@mui/material/List";
// import ListItem from "@mui/material/ListItem";
// import ListItemText from "@mui/material/ListItemText";
// import IconButton from "@mui/material/IconButton";
import { useScreenshot, createFileName } from "use-react-screenshot";
import Switch from "@mui/material/Switch";
import Modal from "@mui/material/Modal";

import Graph from "../components/Graph.js";
import { parseGraph } from "../util/GraphParser.js";

function MainPage(props: {
  websocketAll: WebSocket | null;
  websocketFodina: WebSocket | null;
  model: string;
}) {
  const ref = useRef<HTMLDivElement>(null);

  const [image, takeScreenshot] = useScreenshot({
    type: "image/jpeg",
    quakity: 1.0,
  });

  const downloadScreenshot = (image: string) => {
    const timestamp = Date.now();
    const currentDate = new Date(timestamp);
    const formattedDate = `${currentDate
      .getDate()
      .toString()
      .padStart(2, "0")}-${(currentDate.getMonth() + 1)
      .toString()
      .padStart(2, "0")}-${currentDate.getFullYear()}_${currentDate
      .getHours()
      .toString()
      .padStart(2, "0")}-${currentDate
      .getMinutes()
      .toString()
      .padStart(2, "0")}-${currentDate
      .getSeconds()
      .toString()
      .padStart(2, "0")}`;
    const extension = "jpg";

    const a = document.createElement("a");
    a.href = image;
    a.download = createFileName(extension, formattedDate);
    a.click();
  };

  //Updating graph
  const [updateEveryEvent, setUpdateEveryEvent] = useState(false);
  const [updateXEvents, setUpdateXEvents] = useState(false);
  const [updateXEventsValue, setUpdateXEventsValue] = useState(-1);
  const [updateXSeconds, setUpdateXSeconds] = useState(false);
  const [updateXSecondsValue, setUpdateXSecondsValue] = useState(-1);

  //Datastructure to store events
  const [useSpaceSaving, setUseSpaceSaving] = useState(false);
  const [useLossyCounting, setUseLossyCounting] = useState(false);
  const [datastructureMax, setDatastructureMax] = useState(-1);

  //Fodina Settings
  const [mineDuplicates, setMineDuplicates] = useState(false);
  const [noL2LWithL1l, setNoL2lWithL1l] = useState(false);
  const [noBinaryConflicts, setNoBinaryConflicts] = useState(false);
  const [connectNet, setConnectNet] = useState(false);
  const [mineLongDependencies, setMineLongDependencies] = useState(false);

  //Fodina Thresholds
  const [td, setTd] = useState(-1);
  const [tl1l, setTl1l] = useState(-1);
  const [tl2l, setTl2l] = useState(-1);
  const [tld, setTld] = useState(-1);

  //The Screenshots taken from the graph
  //const [screenshots, setScreenshots] = useState<string[]>([]);

  //The Analytics Info
  const [selectedElement, setSelectedElement] = useState("");
  const [selectedElementFirst, setSelectedElementFirst] = useState("");
  const [selectedElementLast, setSelectedElementLast] = useState("");
  const [selectedElementAverage, setSelectedElementAverage] = useState("");
  const [selectedElementMedian, setSelectedElementMedian] = useState("");
  const [selectedElementLabel, setSelectedElementLabel] = useState("");

  const [graphData, setGraphData] = useState({});
  //So that the graph updates upon receiving data
  const [uniqueGraphKey, setUniqueGraphKey] = useState(-1);

  const [modalOpen, setModalOpen] = useState(false);

  const handleModalOpen = () => setModalOpen(true);
  const handleModalClose = () => setModalOpen(false);

  const updateSelectionData = (
    pSelectedElement: string,
    pFirst: string,
    pLast: string,
    pAverage: string,
    pMedian: string,
    label: string
  ) => {
    console.log(
      `Received ${pSelectedElement}, first seen at ${pFirst}, last seen at ${pLast}`
    );

    setSelectedElement(pSelectedElement);
    setSelectedElementFirst(pFirst);
    setSelectedElementLast(pLast);
    setSelectedElementAverage(pAverage);
    setSelectedElementMedian(pMedian);
    setSelectedElementLabel(label);

    console.log(`Selected Element: ${selectedElement}`);
    console.log(`First Seen: ${selectedElementFirst}`);
    console.log(`Last Seen: ${selectedElementLast}`);
  };

  //Return all the configuration options that were given by user
  const createConfigurationJSON = () => {
    const configValues = {
      paramUpdateEveryEvent: updateEveryEvent,
      paramUpdateXEvents: updateXEvents,
      paramUpdateXEventsValue: updateXEventsValue,
      paramUpdateXSeconds: updateXSeconds,
      paramUpdateXSecondsValue: updateXSecondsValue,
      paramUseSpaceSaving: useSpaceSaving,
      paramUseLossyCounting: useLossyCounting,
      paramDataStructureMax: datastructureMax,
      paramMineDuplicates: mineDuplicates,
      paramNoL2LWithL1l: noL2LWithL1l,
      paramNoBinaryConflicts: noBinaryConflicts,
      paramConnectNet: connectNet,
      paramMineLongDependencies: mineLongDependencies,
      paramTd: td,
      paramTl1l: tl1l,
      paramTl2l: tl2l,
      paramTld: tld,
      paramUseExperimental: SBAR,
    };

    const filteredConfig = Object.fromEntries(
      Object.entries(configValues)
        //Filter everything that is not the default value
        .filter(([key, value]) => {
          return value !== false && value !== -1;
        })
    );

    return JSON.stringify(filteredConfig);
  };

  const runFodina = function (pMessage: string, pData: any) {
    if (props.websocketFodina && props.websocketFodina !== null) {
      let messageData = {};

      messageData = { message: pMessage, data: JSON.stringify(pData) };

      props.websocketFodina.send(JSON.stringify(messageData));
      props.websocketFodina.onmessage = (event: { data: string }) => {
        console.log(event.data);
        if (
          event.data.includes("strict digraph") &&
          event.data.includes("graph [bb=")
        ) {
          const graphDataNew = parseGraph(event.data);
          setGraphData(graphDataNew);
          setUniqueGraphKey(Math.random() * 100);

          return;
        } else if (event.data.includes("strict digraph")) {
          const graphDataNew = parseGraph(event.data);
          setGraphData(graphDataNew);
          setUniqueGraphKey(Math.random() * 100);
        } else {
          console.error("Something went wrong here");
        }
      };
    } else {
      console.log("Socket Dead");
    }
  };

  const [instanceRunning, setInstanceRunning] = useState(false);

  //Send Configuration to the backend
  const sendConfigurationToBackend = function () {
    setInstanceRunning(true);
    runFodina("runInstance", {
      config: createConfigurationJSON(),
      model: props.model,
    });
  };

  //Disable the Run-Button when the mandatory options are not set
  const disableButton = () => {
    return (
      instanceRunning ||
      !(
        updateEveryEvent ||
        (updateXEvents && updateXEventsValue > 0) ||
        (updateXSeconds && updateXSecondsValue > 0)
      ) ||
      (SBAR && !((useLossyCounting || useSpaceSaving) && datastructureMax > 0))
    );
  };

  const createScreenshot = () =>
    takeScreenshot(ref.current).then(downloadScreenshot);

  //See comment in the JSP Code

  // //Add the new screenshot to the list
  // const addScreenshotToList = (newTimestamp: string) => {
  //   //Has to be done like this, because JS checks for reference equivalence
  //   const screenshotsCurr = [...screenshots];
  //   screenshotsCurr.push(newTimestamp);
  //   setScreenshots(screenshotsCurr);
  // };

  // //Delete Screenshot
  // const deleteScreenshot = (value: string) => {
  //   const screenshotsCurr = screenshots;
  //   const screenshotsNew = screenshotsCurr.filter((elem) => {
  //     return elem !== value;
  //   });
  //   setScreenshots(screenshotsNew);
  // };

  const [SBAR, setSBAR] = useState(false);

  const handleSwitch = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSBAR(event.target.checked);
  };

  return (
    <div className="wrapper">
      <div className="container">
        <div className="graph">
          <div className="graph-content" id="graph-content" ref={ref}>
            <Graph
              key={uniqueGraphKey}
              graphData={graphData}
              selectionUpdater={updateSelectionData}
            />
          </div>
        </div>
        {/* Analytics Area ======================================================================================== */}
        <div className="analysis">
          <div className="analysis-header">
            <div className="analysis-header-icon">
              <AnalyticsIcon sx={{ width: "70%", height: "70%" }} />
            </div>
            <h1 style={{ fontSize: "40px", whiteSpace: "nowrap" }}>
              Analytics: {selectedElement}{" "}
              {selectedElement != "" ? "-> ' " : ""}
              {selectedElementLabel} {selectedElement != "" ? "'" : ""}
            </h1>
          </div>
          <div className="analysis-metric-wrapper">
            <div className="analysis-metric-element">
              <h3>Earliest</h3>
              {selectedElementFirst}
            </div>
            <div className="analysis-metric-element">
              <h3>Average</h3>
              {selectedElementAverage}
            </div>
            <div className="analysis-metric-element">
              <h3>Median</h3>
              {selectedElementMedian}
            </div>
            <div className="analysis-metric-element">
              <h3>Latest</h3>
              {selectedElementLast}
            </div>
          </div>
          <div className="analysis-graph-saving">
            <div className="analysis-graph-saving-icon">
              <CameraAltIcon sx={{ width: "50%", height: "50%" }} />
            </div>
            {/* Idea was to allow multiple screenshots to be done before saving them alltogether. I thought this would be practical, as for instances where a lot a change happens to the graph quickly. In such cases one could first track the evolution of the graph and take screenshots, which could then be saved later with the choice of the path where to save it to (again better than spamming them all in your download folder)
            This idea has been put off though, due to time issues and replaced with the (imo) not so pretty variant of saving to the download-folder and only one at a time*/}

            {/* <div className="analysis-graph-saving-screenshots-wrapper">
              <div className="analysis-graph-saving-screenshot-component">
                <List
                  dense
                  sx={{
                    width: "100%",
                    maxWidth: 360,
                    bgcolor: "background.paper",
                  }}
                >
                  {screenshots.map((value) => (
                    <ListItem
                      key={value}
                      secondaryAction={
                        <IconButton
                          onClick={(e) => {
                            deleteScreenshot(value);
                          }}
                        >
                          <DeleteIcon />
                        </IconButton>
                      }
                    >
                      <ListItemText
                        primary={value}
                        primaryTypographyProps={{ fontSize: "12px" }}
                      />
                    </ListItem>
                  ))}
                </List>
              </div>
            </div> 
            <div className="analysis-graph-saving-buttons">
              <Button
                variant="contained"
                sx={{
                  width: "80%",
                  height: "25%",
                  background: "gray",
                  fontSize: "10px",
                }}
                onClick={(e) => {
                  createScreenshot();
                }}
              >
                Screenshot
              </Button>
              <Button
                variant="contained"
                sx={{
                  width: "80%",
                  height: "25%",
                  background: "gray",
                  fontSize: "10px",
                }}
                onClick={(e) => {
                  console.log("Click");
                }}
                disabled={screenshots.length == 0}
              >
                Save
              </Button>
            </div>*/}
            <div className="analysis-graph-saving-button">
              <Button
                variant="contained"
                sx={{
                  width: 250,
                  height: 80,
                  background: "gray",
                  marginLeft: "12%",
                }}
                onClick={(e) => {
                  createScreenshot();
                }}
              >
                Take Screenshot
              </Button>
            </div>
          </div>
        </div>
        {/* Settings Area ======================================================================================== */}
        <div className="config">
          <div className="settings-wrapper">
            <div className="settings-icon">
              <SettingsIcon sx={{ width: "60%", height: "60%" }} />
              <Switch onChange={handleSwitch} />
              S-BAR (experimental)
              <InfoIcon onClick={handleModalOpen} />
              <Modal
                open={modalOpen}
                onClose={handleModalClose}
                aria-labelledby="modal-modal-title"
                aria-describedby="modal-modal-description"
              >
                <div className="sbar-modal-text">
                  <div className="sbar-modal-headline">
                    <b>Problems with S-BAR</b>
                  </div>
                  <div>
                    S-BAR is the framework presented in "Event stream-based
                    process discovery using abstract representations" by
                    Sebastiaan J. van Zelst et. al. <br />
                    Easily said it works with maintaining two datastructures,
                    that hold information regarding the events that were
                    received in a event stream and that form a abstract
                    representation of the behavior of the process that emits
                    this event stream. These datastructures then form the input
                    for the 'classical' process discovery algorithms.
                    <br />
                    <br /> The maintanance of the datastructures is done by
                    looking at one received event at a time and thus it does not
                    track any event traces, which leads to the following problem
                    regarding the Fodina-Algorithm: <br />
                    <br />
                    In Fodinas last step, the event traces are used to determine
                    input- and output-bindings of the activities that are part
                    of the events that were used for the discovery of a process
                    model, which is a crucial step in the differentiation of XOR
                    and AND gates. <br />
                    For this it uses a precomputed abstraction (follows-graph),
                    that is done in the previous steps of the Fodina algorithm.{" "}
                    <br />
                    While the S-BAR architecture also computes parts of the
                    needed abstraction, some configuration options for Fodina
                    cannot be used with this method: <br />
                    <br />
                    <li>
                      Mine Duplicate Tasks: relies on local context of a
                      activity inside a event trace
                    </li>
                    <li>
                      MineLongDependencies: needs indirectSuccessionCount, a
                      measure that represents eventual succession and would need
                      the complete event traces
                    </li>
                    <br />
                    While point 2 might be able to be implemented with a few
                    extensions of S-BAR, the mining of duplicate tasks and the
                    computation of the input and output bindings for the
                    activities will need further research.
                    <br />
                    <br /> For those reasons it was not possible for me to
                    create a fully working implementation in time and I decided
                    to restrict the execution to the generation of the
                    directly-follows-abstraction. <br /> <br />
                    <b>
                      The user can choose between the process discovery with
                      classical Fodina, where event traces were generated from
                      the event stream or the computation of the
                      directly-follows abstraction using S-BAR with limited
                      configuration options from the Fodina algorithm
                    </b>
                  </div>
                </div>
              </Modal>
            </div>
            <div className="settings-update-wrapper settings-group-wrapper">
              <h3>
                <u>Update Settings</u>
              </h3>
              <div>
                <div className="settings-label">
                  <Checkbox
                    sx={{
                      "&.Mui-checked": {
                        color: "gray",
                      },
                    }}
                    onClick={(e) => {
                      setUpdateEveryEvent(!updateEveryEvent);
                      setUpdateXEvents(false);
                      setUpdateXSeconds(false);
                      setUpdateXEventsValue(-1);
                      setUpdateXSecondsValue(-1);
                    }}
                    checked={updateEveryEvent}
                  />
                  Update on every event
                </div>
                <div className="settings-label">
                  <Checkbox
                    sx={{
                      "&.Mui-checked": {
                        color: "gray",
                      },
                    }}
                    onClick={(e) => {
                      setUpdateEveryEvent(false);
                      setUpdateXEvents(!updateXEvents);
                      setUpdateXSeconds(false);
                      setUpdateXSecondsValue(-1);
                    }}
                    checked={updateXEvents}
                  />
                  Update after{" "}
                  <input
                    type="number"
                    style={{
                      width: 30,
                      marginLeft: "10px",
                      marginRight: "10px",
                    }}
                    disabled={!updateXEvents}
                    onChange={(e) => {
                      const value = isNaN(e.target.valueAsNumber)
                        ? -1
                        : e.target.valueAsNumber;
                      setUpdateXEventsValue(value);
                    }}
                    value={updateXEventsValue == -1 ? "" : updateXEventsValue}
                  ></input>{" "}
                  events
                </div>
                <div className="settings-label">
                  <Checkbox
                    sx={{
                      "&.Mui-checked": {
                        color: "gray",
                      },
                    }}
                    onClick={(e) => {
                      setUpdateEveryEvent(false);
                      setUpdateXEvents(false);
                      setUpdateXEventsValue(-1);
                      setUpdateXSeconds(!updateXSeconds);

                      console.log(updateXEventsValue);
                    }}
                    checked={updateXSeconds}
                  />
                  Update after{" "}
                  <input
                    type="number"
                    style={{
                      width: 30,
                      marginLeft: "10px",
                      marginRight: "10px",
                    }}
                    disabled={!updateXSeconds}
                    onChange={(e) => {
                      const value = isNaN(e.target.valueAsNumber)
                        ? -1
                        : e.target.valueAsNumber;
                      setUpdateXSecondsValue(value);
                    }}
                    value={updateXSecondsValue == -1 ? "" : updateXSecondsValue}
                  ></input>{" "}
                  seconds
                </div>
              </div>
            </div>
            <div
              className="settings-datastructure-wrapper settings-group-wrapper"
              style={{
                backgroundColor: !SBAR ? "#b3b3b3" : "",
                color: !SBAR ? "#646464" : "",
              }}
            >
              <h3>
                <u>Datastructure Settings</u>
              </h3>
              <div>
                <div className="settings-label">
                  <Checkbox
                    sx={{
                      "&.Mui-checked": {
                        color: "gray",
                      },
                    }}
                    disabled={!SBAR}
                    onClick={(e) => {
                      setUseLossyCounting(false);
                      setUseSpaceSaving(!useSpaceSaving);
                    }}
                    checked={useSpaceSaving}
                  />
                  Use SpaceSaving
                </div>
                <div className="settings-label">
                  <Checkbox
                    sx={{
                      "&.Mui-checked": {
                        color: "gray",
                      },
                    }}
                    disabled={!SBAR}
                    onClick={(e) => {
                      setUseLossyCounting(!useLossyCounting);
                      setUseSpaceSaving(false);
                    }}
                    checked={useLossyCounting}
                  />
                  Use Lossy Counting
                </div>
                <div className="settings-datastructure-max">
                  <b>Maximum Size</b>
                  <input
                    type="number"
                    style={{
                      width: 30,
                      marginLeft: "10px",
                      marginRight: "10px",
                      marginTop: "10px",
                    }}
                    disabled={!SBAR}
                    onChange={(e) => {
                      const value = isNaN(e.target.valueAsNumber)
                        ? -1
                        : e.target.valueAsNumber;
                      setDatastructureMax(value);
                    }}
                    value={datastructureMax == -1 ? "" : datastructureMax}
                  ></input>{" "}
                </div>
              </div>
            </div>
            <div className="settings-algorithm-wrapper settings-group-wrapper">
              <h3>
                <u>Fodina Settings</u>
              </h3>
              <div>
                <div
                  className="settings-label"
                  style={{
                    color: SBAR ? "#646464" : "",
                  }}
                >
                  <Checkbox
                    sx={{
                      "&.Mui-checked": {
                        color: "gray",
                      },
                    }}
                    disabled
                    onClick={(e) => {
                      setMineDuplicates(!mineDuplicates);
                    }}
                  />
                  MineDuplicates
                </div>
                <div className="settings-label">
                  <Checkbox
                    sx={{
                      "&.Mui-checked": {
                        color: "gray",
                      },
                    }}
                    onClick={(e) => {
                      setNoL2lWithL1l(!noL2LWithL1l);
                    }}
                  />
                  NoL2LWithL1l
                </div>
                <div className="settings-label">
                  <Checkbox
                    sx={{
                      "&.Mui-checked": {
                        color: "gray",
                      },
                    }}
                    onClick={(e) => {
                      setNoBinaryConflicts(!noBinaryConflicts);
                    }}
                  />
                  NoBinaryConflicts
                </div>
                <div className="settings-label">
                  <Checkbox
                    sx={{
                      "&.Mui-checked": {
                        color: "gray",
                      },
                    }}
                    onClick={(e) => {
                      setConnectNet(!connectNet);
                    }}
                  />
                  ConnectNet
                </div>
                <div
                  className="settings-label"
                  style={{
                    color: SBAR ? "#646464" : "",
                  }}
                >
                  <Checkbox
                    sx={{
                      "&.Mui-checked": {
                        color: "gray",
                      },
                    }}
                    disabled={SBAR}
                    onClick={(e) => {
                      setMineLongDependencies(!mineLongDependencies);
                    }}
                  />
                  MineLongDependencies
                </div>
              </div>
            </div>
            <div className="settings-threshold-wrapper settings-group-wrapper">
              <h3>
                <u>Fodina Thresholds</u>
              </h3>
              <div>
                <div className="settings-label-fodinathres">
                  t_d
                  <input
                    type="number"
                    style={{
                      width: 40,
                      height: 18,
                      marginLeft: "10px",
                    }}
                    onChange={(e) => {
                      const value = isNaN(e.target.valueAsNumber)
                        ? -1
                        : e.target.valueAsNumber;
                      setTd(value);
                    }}
                  ></input>
                </div>
                <div className="settings-label-fodinathres">
                  t_l1l
                  <input
                    type="number"
                    style={{
                      width: 40,
                      height: 18,
                      marginLeft: "10px",
                    }}
                    onChange={(e) => {
                      const value = isNaN(e.target.valueAsNumber)
                        ? -1
                        : e.target.valueAsNumber;
                      setTl1l(value);
                    }}
                  ></input>
                </div>
                <div className="settings-label-fodinathres">
                  t_l2l
                  <input
                    type="number"
                    style={{
                      width: 40,
                      height: 18,
                      marginLeft: "10px",
                    }}
                    onChange={(e) => {
                      const value = isNaN(e.target.valueAsNumber)
                        ? -1
                        : e.target.valueAsNumber;
                      setTl2l(value);
                    }}
                  ></input>
                </div>
                <div
                  className="settings-label-fodinathres"
                  style={{
                    color: SBAR ? "#646464" : "",
                  }}
                >
                  t_ld
                  <input
                    type="number"
                    style={{
                      width: 40,
                      height: 18,
                      marginLeft: "10px",
                    }}
                    disabled={SBAR}
                    onChange={(e) => {
                      const value = isNaN(e.target.valueAsNumber)
                        ? -1
                        : e.target.valueAsNumber;
                      setTld(value);
                    }}
                  ></input>
                </div>
              </div>
            </div>
          </div>
          <div className="runbutton-wrapper">
            <Button
              variant="contained"
              disabled={disableButton()}
              sx={{ width: 250, height: 80, background: "gray" }}
              onClick={(e) => {
                sendConfigurationToBackend();
              }}
            >
              Start Execution
            </Button>
            {disableButton() && !instanceRunning ? (
              <div>
                You must still choose an option for at least one of the settings
                or enter a valid value
                {/* (TODO: thresholds mit default oder als pflicht?) */}
              </div>
            ) : null}
          </div>
        </div>
      </div>
    </div>
  );
}

export default MainPage;
