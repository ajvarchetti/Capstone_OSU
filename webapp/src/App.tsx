import { useState, useEffect } from "react";
import "./App.css";

function App()  {
  const [theory, setTheory] = useState('');
  const [input1, setInput1] = useState('');
  const [input2, setInput2] = useState('');
  const [responses, setResponses] = useState<{ title: string; content: string }[]>(() => {
    const storedResponses = localStorage.getItem("responses");
    return storedResponses ? JSON.parse(storedResponses) : [];
  });
  const [activeResponse, setActiveResponse] = useState<number | null>(null);
  const [showResponse, setShowResponse] = useState(false);
  const [hasGenerated, setHasGenerated] = useState(responses.length > 0);
  const isButtonDisabled = !input1.trim() || !input2.trim() || input1.trim().length > 255 || input2.trim().length > 255;

  useEffect(() => {
    localStorage.setItem("responses", JSON.stringify(responses));
  }, [responses]);

  const generateTheory = async () => {
    if (!input1 || !input2) {
      alert("Please enter two topics.");
      return;
    }
  
    const query = `${input1},${input2}`;
    const apiUrl =
      process.env.NODE_ENV === "production"
        ? "https://conspiragen.com/generate"
        : "http://localhost:5002/generate";

    try {
      const response = await fetch(`${apiUrl}?q=${encodeURIComponent(query)}`);
      const data = await response.json();
  
      if (!response.ok) {
        throw new Error(data.error || "Failed to generate theory");
      }
  
      const newTheory = data.generated_conspiracy;
      const title = data.keywords.join(" and ");
  
      setTheory(newTheory);
      setResponses([...responses, { title, content: newTheory }]);
      setActiveResponse(responses.length);
      setShowResponse(true);
      setHasGenerated(true);
    } catch (error: unknown) {
      if (error instanceof Error) {
        alert(error.message);
      } else {
        alert("An unknown error occurred.");
      }
      console.error("Fetch error:", error);
    }
  };

  const startNewTheory = () => {
    setInput1('');
    setInput2('');
    setTheory('');
    setShowResponse(false);
    setActiveResponse(null);
  };

  const clearHistory = () => {
    setResponses([]); // Reset state
    localStorage.removeItem("responses"); // Clear localStorage
    setHasGenerated(false); // Hide sidebar
  };

  return (
    <div className="container">
      {hasGenerated && (
        <div className="sidebar">
          <div>
            <div className="stored-responses-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <h2 className="stored-responses" style={{ margin: 0 }}>Stored Responses</h2>
              <button 
              onClick={() => {
                if (window.confirm('Are you sure you want to clear the response history? This action cannot be undone.')) {
                  clearHistory();
                }
              }}
              title="Clear History" 
              style={{ background: 'none', border: 'none', cursor: 'pointer'}}
              >🗑️</button>
            </div>
            <hr className="stored-responses-line"/>
            <ul className="response-list" style={{ padding: 0, margin: 0 }}>
              {responses.map((resp, index) => (
                <li
                  key={index}
                  className={`response-item ${activeResponse === index ? 'active' : ''}`}
                  onClick={() => { setTheory(resp.content); setShowResponse(true); setActiveResponse(index); }}
                  title={resp.title}
                  style={{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis'}}
                >
                  {resp.title}
                </li>
              ))}
            </ul>
          </div>
          <button onClick={startNewTheory} className="button new-theory-button">New Theory</button>
        </div>
      )}

      <div className="main-content">
      
        <img className="main-logo" src="favicon.png"/>

        <h1 className="title">Conspiragen</h1>
        {!showResponse ? (

          <div>

            <div className="intro-text">
              <span>To generate a conspiracy theory between two topics, enter the topics in the boxes below!</span>
            </div>

            <div className = "inputs">
              <input
                type="text"
                value={input1}
                onChange={(e) => setInput1(e.target.value)}
                placeholder="First Topic"
                className="input-field"
                style={{ margin: '0 32px' }}
              />

              <input
                type="text"
                value={input2}
                onChange={(e) => setInput2(e.target.value)}
                placeholder="Second Topic"
                className="input-field"
                style={{ margin: '0 32px' }}
              />
            </div>

            <div className="button-container">
              <button
                onClick={generateTheory}
                className={isButtonDisabled ? "button disabled-button" : "button generate-button"}
                disabled={isButtonDisabled}
              >
                Generate Theory
              </button>
            </div>
          </div>
        ) : (
          <div className="text-center">
            <h2 className="header-text">Response</h2>
            <p className="response-box">{theory}</p>
          </div>
        )}
        {showResponse ? (
          <div>
            <br></br>
            <button onClick={startNewTheory} className="button centered-theory-button">New Theory</button>
          </div>
        ) : null}
      </div>
    </div>
  );
}

export default App;
