import React, { useEffect, useState } from "react";
import Box from "@mui/material/Box";
import Tabs from "@mui/material/Tabs";
import Tab from "@mui/material/Tab";

import MainPage from "./MainPage";

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function a11yProps(index: number) {
  return {
    id: `simple-tab-${index}`,
    "aria-controls": `simple-tabpanel-${index}`,
  };
}

function index() {
  const [value, setValue] = React.useState(0);

  const [socketAll, setSocketAll] = useState<WebSocket | null>(null);
  const [socketAllInstantiated, setSocketAllInstantiated] = useState(false);

  const [socketFodina, setSocketFodina] = useState<WebSocket | null>(null);
  const [socketFodinaInstantiated, setSocketFodinaInstantiated] =
    useState(false);

  const handleChange = (event: React.SyntheticEvent, newValue: number) => {
    setValue(newValue);
  };

  //Referenz----------------------------------------------------------------
  const [filenames, setFilenames] = useState([]);

  useEffect(() => {
    const newSocket = new WebSocket("ws://localhost:8080/");

    newSocket.onopen = () => {
      setSocketAllInstantiated(true);
    };

    newSocket.onclose = () => {
      console.log("WebSocket connection closed");
    };

    setSocketAll(newSocket);

    const newSocketFodina = new WebSocket("ws://localhost:8081/");

    newSocketFodina.onopen = () => {
      setSocketFodinaInstantiated(true);
    };

    newSocketFodina.onclose = () => {
      console.log("WebSocket connection closed");
    };

    setSocketFodina(newSocketFodina);
  }, []);

  const getFiles = (socket: WebSocket | null) => {
    if (socket && socket !== null) {
      socket.onmessage = (event: { data: string }) => {
        setFilenames(JSON.parse(event.data.replace(/'/g, '"')));
      };
    } else {
      console.log("Socket Dead");
    }
  };

  useEffect(() => {
    if (socketAllInstantiated) {
      socketAll?.send(JSON.stringify({ message: "getFiles" }));
      getFiles(socketAll);
    }
  }, [socketAllInstantiated]);

  //-------------------------------------------------------------------------

  return (
    <Box sx={{ width: "100%" }}>
      <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
        <Tabs
          value={value}
          onChange={handleChange}
          aria-label="basic tabs example"
          centered
        >
          {filenames.map((filename: string, index: number) => (
            <Tab key={filename} label={filename} {...a11yProps(index)} />
          ))}
        </Tabs>
      </Box>
      <MainPage
        websocketAll={socketAll}
        websocketFodina={socketFodina}
        model={filenames[value]}
      />
    </Box>
  );
}

export default index;
