import { useState } from "react";
import "./App.css";

function App()  {
  const [theory, setTheory] = useState('');
  const [input1, setInput1] = useState('');
  const [input2, setInput2] = useState('');
  const [responses, setResponses] = useState<{ title: string; content: string }[]>([]);
  const [activeResponse, setActiveResponse] = useState<number | null>(null);
  const [showResponse, setShowResponse] = useState(false);
  const [hasGenerated, setHasGenerated] = useState(false);
  const isButtonDisabled = !input1.trim() || !input2.trim() || input1.trim().length>250 || input2.trim().length>250;

  const generateTheory = () => {
    const newTheory = `What if ${input1} and ${input2} are secretly connected through an ancient organization?`;
    const title = `${input1} and ${input2}`;
    setTheory(newTheory);
    setResponses([...responses, { title, content: newTheory }]);
    setActiveResponse(responses.length);
    setShowResponse(true);
    setHasGenerated(true);
  };

  const startNewTheory = () => {
    setInput1('');
    setInput2('');
    setTheory('');
    setShowResponse(false);
    setActiveResponse(null);
  };

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
          </div>
        ) : (
          <div className="text-center">
            <h2 className="header-text">Response</h2>
            <p className="response-box">{theory}</p>
            <button onClick={startNewTheory} className="button new-theory-button">New Theory</button>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
