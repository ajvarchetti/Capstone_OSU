import { useState } from "react";
import "./App.css";
import DOMPurify from 'dompurify';

function App()  {
  const [theory, setTheory] = useState('');
  const [input1, setInput1] = useState('');
  const [input2, setInput2] = useState('');
  const [responses, setResponses] = useState<{ title: string; content: string }[]>([]);
  const [activeResponse, setActiveResponse] = useState<number | null>(null);
  const [showResponse, setShowResponse] = useState(false);
  const [hasGenerated, setHasGenerated] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const isButtonDisabled = !input1.trim() || !input2.trim() || isProcessing;

  const generateTheory = async () => {
    if (!input1 || !input2) {
      alert("Please enter two topics.");
      return;
    }

    setIsProcessing(true);
  
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
    } finally {
      setIsProcessing(false); 
    }
  };

  const startNewTheory = () => {
    setInput1('');
    setInput2('');
    setTheory('');
    setShowResponse(false);
    setActiveResponse(null);
  };

  const sanitizeInput = (input: string): string => {
    let sanitized = DOMPurify.sanitize(input.trim()); 
    return sanitized.replace(/[^a-zA-Z0-9\s]/g, "").slice(0, 50);
};

  return (
    <div className="container">
      {hasGenerated && (
        <div className="sidebar">
          <div>
            <h2 className="stored-responses">Stored Responses</h2>
            <hr className="stored-responses-line"></hr>
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
                  onChange={(e) => setInput1(sanitizeInput(e.target.value))} 
                  placeholder="First Topic" 
                  className="input-field"
                  style={{ margin: '0 32px' }}
                  onKeyDown={(e) => {
                  if (e.key === "Enter" && !isButtonDisabled) {
                    generateTheory();
                  }
                }}
              />

              <input 
                  type="text" 
                  value={input2} 
                  onChange={(e) => setInput2(sanitizeInput(e.target.value))} 
                  placeholder="Second Topic" 
                  className="input-field"
                  style={{ margin: '0 32px' }}
                  onKeyDown={(e) => {
                  if (e.key === "Enter" && !isButtonDisabled) {
                    generateTheory();
                  }
                }}
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
      </div>
    </div>
  );
}

export default App;
