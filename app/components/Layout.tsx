'use client';

import { useState, useCallback, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '../store';
import { addMessage, setMessages } from '../store/chatSlice';
import { addPath, setSelectedTool } from '../store/canvasSlice';

interface Message {
  id: number;
  text: string;
  sender: 'user' | 'system';
}

export default function Layout() {
  const dispatch = useDispatch();
  const messages = useSelector((state: RootState) => state.chat.messages);
  const [error, setError] = useState<string | null>(null);
  const [layoutClass, setLayoutClass] = useState<string>('');
  const [showCanvas, setShowCanvas] = useState(true);
  const [inputMessage, setInputMessage] = useState('');

  const handleResize = useCallback(() => {
    const width = window.innerWidth;
    if (width < 768) {
      setLayoutClass('mobile');
    } else if (width < 1024) {
      setLayoutClass('tablet');
    } else {
      setLayoutClass('desktop');
    }
  }, []);

  useEffect(() => {
    handleResize();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [handleResize]);

  useEffect(() => {
    try {
      const savedMessages = localStorage.getItem('chatMessages');
      if (savedMessages) {
        dispatch(setMessages(JSON.parse(savedMessages)));
      }
    } catch (error) {
      console.error('Error loading saved messages:', error);
    }
  }, [dispatch]);

  const handleMessageSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputMessage.trim()) return;

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: inputMessage }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const newMessage: Message = {
        id: Date.now(),
        text: inputMessage,
        sender: 'user',
      };

      dispatch(addMessage(newMessage));

      try {
        localStorage.setItem('chatMessages', JSON.stringify([...messages, newMessage]));
      } catch (error) {
        console.error('Error saving messages to localStorage:', error);
      }

      setInputMessage('');
      setError(null);
    } catch (error) {
      console.error('Failed to send message:', error);
      setError('Error sending message. Please try again.');
    }
  };

  const handleToolSelect = (tool: string) => {
    dispatch(setSelectedTool(tool));
  };

  const handleCanvasDraw = (path: { type: string; x?: number; y?: number }) => {
    dispatch(addPath(path));
  };

  return (
    <div className={`flex min-h-screen bg-gray-100 ${layoutClass}`} data-testid="layout-container">
      <div className="flex flex-1 flex-col p-4" data-testid="chat-panel">
        <div className="mb-4 flex-1 overflow-y-auto">
          {messages.map(msg => (
            <div
              key={msg.id}
              data-testid="chat-message"
              className={`mb-2 rounded p-2 ${
                msg.sender === 'user' ? 'ml-auto bg-blue-100' : 'bg-gray-100'
              }`}
            >
              {msg.text}
            </div>
          ))}
          {error && (
            <div data-testid="error-message" className="rounded bg-red-50 p-2 text-red-500">
              {error}
            </div>
          )}
        </div>
        <form onSubmit={handleMessageSubmit} className="flex">
          <input
            type="text"
            value={inputMessage}
            onChange={e => setInputMessage(e.target.value)}
            placeholder="Type a message..."
            className="flex-1 rounded-l border p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            data-testid="chat-input"
          />
          <button
            type="submit"
            className="rounded-r bg-blue-500 px-4 py-2 text-white transition-colors hover:bg-blue-600"
          >
            Send
          </button>
        </form>
      </div>

      <div
        className="flex flex-1 flex-col p-4"
        data-testid="canvas-panel"
        style={{ display: showCanvas ? 'block' : 'none' }}
      >
        <canvas
          data-testid="drawing-canvas"
          width={500}
          height={500}
          className="rounded border border-gray-300 shadow-sm"
          onMouseDown={() => handleCanvasDraw({ type: 'start' })}
          onMouseMove={e =>
            handleCanvasDraw({
              type: 'move',
              x: e.clientX,
              y: e.clientY,
            })
          }
          onMouseUp={() => handleCanvasDraw({ type: 'end' })}
        />
        <div className="mt-4 space-x-2">
          <button
            className="rounded bg-gray-200 px-4 py-2 transition-colors hover:bg-gray-300"
            onClick={() => handleToolSelect('pencil')}
          >
            Pencil
          </button>
          <button
            className="rounded bg-gray-200 px-4 py-2 transition-colors hover:bg-gray-300"
            onClick={() => handleToolSelect('eraser')}
          >
            Eraser
          </button>
        </div>
        <button
          className="mt-4 rounded bg-blue-500 px-4 py-2 text-white transition-colors hover:bg-blue-600"
          onClick={() => setShowCanvas(!showCanvas)}
        >
          {showCanvas ? 'Hide Canvas' : 'Show Canvas'}
        </button>
      </div>
    </div>
  );
}
