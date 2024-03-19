function parseGraph(graphData) {
  //First two elements of split can be discarded, as they irrelevant data (headlines and size-stuff) and last one as well, as its only a closing bracket
  const graphDataSplit = graphData.split(";").splice(2);
  graphDataSplit.pop();

  const nodesRst = [];
  const edgesRst = [];

  const nodeData = [];
  const edgeData = [];

  for (const elem of graphDataSplit) {
    if (elem.includes("->")) {
      edgeData.push(elem);
    } else {
      nodeData.push(elem);
    }
  }

  for (const elem of nodeData) {
    //Position Attributes
    const posStart = elem.indexOf("pos=");
    const posEnd = elem.indexOf('",', posStart);
    const posValue = elem.substring(posStart + 5, posEnd);
    const posValueSplit = posValue.split(",");

    //EventInfos -> FirstSeen, LastSeen, etc
    const eventInfoStart = elem.indexOf("[eventInfo=");
    let eventInfoObject = {};

    //If "[eventInfo=" is not found in the data, we can skip the next part
    if (eventInfoStart != -1) {
      const eventInfoEnd = elem.indexOf("}", eventInfoStart);
      let eventInfoValue = elem.substring(eventInfoStart + 13, eventInfoEnd);
      //For some reason this preceeds the median value in the data returned from server
      eventInfoValue = eventInfoValue.replace("\\\n", "");

      const eventInfoSplit = eventInfoValue.split(",");

      eventInfoObject = eventInfoSplit.reduce((acc, elem) => {
        const [key, value] = elem
          .split(/:(.+)/)
          .map((str) => str.trim().replace(/'/g, ""));
        acc[key] = value;
        return acc;
      }, {});
    } else {
      eventInfoObject = {
        firstEvent: "",
        lastEvent: "",
        averageEvent: "",
        medianEvent: "",
      };
    }

    //Remove everything from the first square bracket, as we already got all the relevant data out of it
    //Also remove "" from our transition ids (e.g. "{start}_to_{a}")
    const splicedAndTrimmed = elem
      .substring(0, elem.indexOf("["))
      .trim()
      .replaceAll('"', "");

    console.log(splicedAndTrimmed);

    if (splicedAndTrimmed.includes("_to_")) {
      nodesRst.push({
        data: {
          id: splicedAndTrimmed,
          label: "",
          type: "transition",
          eventInfo: eventInfoObject,
        },
        position: {
          x: parseFloat(posValueSplit[0]),
          y: parseFloat(posValueSplit[1]),
        },
      });
    } else {
      nodesRst.push({
        data: {
          id: splicedAndTrimmed,
          label: splicedAndTrimmed,
          eventInfo: eventInfoObject,
        },
        position: {
          x: parseFloat(posValueSplit[0]),
          y: parseFloat(posValueSplit[1]),
        },
      });
    }
  }

  for (const elem of edgeData) {
    const splicedAndTrimmed = elem
      .substring(0, elem.indexOf("["))
      .trim()
      .replaceAll('"', "");

    const fromTo = splicedAndTrimmed.split(" -> ");

    edgesRst.push({
      data: { source: fromTo[0], target: fromTo[1], label: "Test" },
    });
  }

  return { nodes: nodesRst, edges: edgesRst };
}

export { parseGraph };
