import { useState } from "react";
import "./App.css";

function App() {
  const [topic1, setTopic1] = useState("");
  const [topic2, setTopic2] = useState("");
  const [theory, setTheory] = useState("");
  const [history, setHistory] = useState<string[]>([]);

  const generateTheory = () => {
    if (topic1 && topic2) {
      const newTheory = `Did you know that ${topic1} is secretly connected to ${topic2}? The truth is out there!`;
      setTheory(newTheory);
      setHistory([newTheory, ...history]); // Add new theory to history
      setTopic1(""); // Clear input fields
      setTopic2("");
    } else {
      setTheory("Please enter two topics to generate a theory.");
    }
  };

  return (
    <div className="container">
      {/* Left Sidebar for History */}
      <div className="history">
        <h2 className="text-xl font-bold">Theory History</h2>
        <ul>
          {history.map((item, index) => (
            <li key={index} className="history-item">
              {item}
            </li>
          ))}
        </ul>
      </div>

      {/* Main Content */}
      <div className="main">
        <h1 className="text-3xl font-bold mb-6">Conspiragen</h1>
        <p>Enter two topics to create a conspiracy theory linking them together:</p>
        <p>
          <input
            type="text"
            value={topic1}
            onChange={(e) => setTopic1(e.target.value)}
            placeholder="First topic"
          />{" "}
          and{" "}
          <input
            type="text"
            value={topic2}
            onChange={(e) => setTopic2(e.target.value)}
            placeholder="Second topic"
          />
        </p>
        <div className="card">
          <button onClick={generateTheory}>Create Theory</button>
        </div>
        {theory && <p className="mt-4">{theory}</p>}
      </div>
    </div>
  );
}

export default App;
