import CytoscapeComponent from "react-cytoscapejs";

const layout = {
  // name: "breadthfirst",
  name: "preset",
  fit: true,
  directed: true,
  padding: 40,
  //animate: true,
  //animationDuration: 500,
  avoidOverlap: true,
  nodeDimensionsIncludeLabels: false,
};

const styleSheet = [
  {
    selector: "node",
    style: {
      backgroundColor: "gray",
      width: 50,
      height: 50,
      "text-halign": "center",
      "text-valign": "center",
      label: "data(label) ",
      "z-index": "10",
      "text-outline-color": "gray",
      "text-outline-width": "2px",
      color: "white",
      fontSize: 20,
    },
  },
  {
    selector: "node[type='transition']",
    style: {
      shape: "rectangle",
      width: 40,
      height: 30,
    },
  },
  {
    selector: "node:selected",
    style: {
      "background-color": "#DC143C",
      width: 70,
      height: 70,
      //text props
      "text-outline-color": "#DC143C",
      "text-outline-width": 5,
    },
  },
  {
    selector: "edge",
    style: {
      width: 3,
      "line-color": "#556b2f",
      "target-arrow-color": "#556b2f",
      "target-arrow-shape": "triangle",
      "curve-style": "bezier",
    },
  },
];

function Graph(props) {
  return (
    <CytoscapeComponent
      key={props.key}
      elements={CytoscapeComponent.normalizeElements(props.graphData)}
      style={{ width: "100%", height: "100%" }}
      zoomingEnabled={true}
      maxZoom={3}
      minZoom={0.25}
      autounselectify={false}
      boxSelectionEnabled={true}
      layout={layout}
      stylesheet={styleSheet}
      cy={(cy) => {
        cy.on("tap", "node", (evt) => {
          var nodeData = evt.target.data();
          console.log(nodeData);

          props.selectionUpdater(
            nodeData.label,
            nodeData.eventInfo.firstEvent,
            nodeData.eventInfo.lastEvent,
            nodeData.eventInfo.averageEvent,
            nodeData.eventInfo.medianEvent,
            nodeData.eventInfo.activityLabel
          );
        });
      }}
    />
  );
}

export default Graph;
