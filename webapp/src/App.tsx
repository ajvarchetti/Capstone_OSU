import { useState, useEffect } from "react";
import "./App.css";

function App()  {
  const [theory, setTheory] = useState('');
  const [input1, setInput1] = useState('');
  const [input2, setInput2] = useState('');
  const [responses, setResponses] = useState<{ title: string; content: string }[]>([]);
  const [activeResponse, setActiveResponse] = useState<number | null>(null);
  const [showResponse, setShowResponse] = useState(false);
  const [hasGenerated, setHasGenerated] = useState(false);
  const isButtonDisabled = !input1.trim() || !input2.trim();
  const [sampleTopics, setSampleTopics] = useState<string[]>([]);

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

  useEffect(() => {
    const fetchSamples = async () => {
      const apiUrl =
        process.env.NODE_ENV === "production"
          ? "https://conspiragen.com/samples"
          : "http://localhost:5002/samples";
      try {
        const response = await fetch(apiUrl);
        const data = await response.json();
  
        if (!response.ok || !Array.isArray(data)) {
          throw new Error("Failed to fetch samples or unexpected response format");
        }
  
        setSampleTopics(data); // <- fix here
      } catch (error: unknown) {
        if (error instanceof Error) {
          alert(error.message);
        } else {
          alert("An unknown error occurred.");
        }
        console.error("Fetch error:", error);
      }
    };
  
    fetchSamples();
  }, []);

  const fillRandomTopics = () => {
    const randomIndex1 = Math.floor(Math.random() * sampleTopics.length);
    let randomIndex2;
  
    do {
      randomIndex2 = Math.floor(Math.random() * sampleTopics.length);
    } while (randomIndex2 === randomIndex1);
  
    setInput1(sampleTopics[randomIndex1]);
    setInput2(sampleTopics[randomIndex2]);
  }
  

  return (
    <div className="container">
      {hasGenerated && (
        <div className="sidebar">
          <div>
            <h2 className="stored-responses">Stored Responses</h2>
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
          <div className="text-center">
            <div className="flex items-center justify-center space-x-2 mb-4">
              <span>Generate Conspiracy Theory between</span>
              <input 
                type="text" 
                value={input1} 
                onChange={(e) => setInput1(e.target.value)} 
                placeholder="First Entity" 
                className="input-field"
                style={{ margin: '0 8px' }}
              />
              <span>and</span>
              <input 
                type="text" 
                value={input2} 
                onChange={(e) => setInput2(e.target.value)} 
                placeholder="Second Entity" 
                className="input-field"
                style={{ margin: '0 8px' }}
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
            <div className="button-container">
              <button onClick={fillRandomTopics} className="button random-button">Fill Random Topics</button>
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
