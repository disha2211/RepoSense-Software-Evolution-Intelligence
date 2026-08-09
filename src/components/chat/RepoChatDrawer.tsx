import { useState } from 'react';
import { Sparkles, Send, X, Bot, Loader2 } from 'lucide-react';

import { askRepoSense } from '../services/backendApi';

interface ChatMessage {
  sender: 'ai' | 'user';
  text: string;
  sources?: string[];
  confidence?: string;
}

export const RepoChatDrawer = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      sender: 'ai',
      text:
        'Hello! I am RepoSense GraphRAG Assistant. Ask me anything about this repository.',
    },
  ]);

  const presetQuestions = [
    'How does authentication work?',
    'Which classes are related to authentication?',
    'What changed in the authentication architecture?',
    'Which modules depend on SecurityConfig?',
  ];

  const handleSend = async (textToSend?: string) => {
    const query = (textToSend ?? input).trim();

    if (!query || isLoading) {
      return;
    }

    setMessages((prev) => [
      ...prev,
      {
        sender: 'user',
        text: query,
      },
    ]);

    setInput('');
    setIsLoading(true);

    try {
      const result = await askRepoSense(query, 3);

      setMessages((prev) => [
        ...prev,
        {
          sender: 'ai',
          text: result.answer,
          confidence: result.confidence,
          sources: result.sources,
        },
      ]);
    } catch (error) {
      console.error('GraphRAG request failed:', error);

      setMessages((prev) => [
        ...prev,
        {
          sender: 'ai',
          text:
            error instanceof Error
              ? error.message
              : 'Failed to get an answer from RepoSense.',
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 flex items-center gap-2 px-5 py-3 rounded-full bg-gradient-to-r from-cyan-500 to-purple-600 text-white font-semibold text-sm shadow-xl shadow-cyan-500/20 hover:scale-105 transition-all z-50 cursor-pointer"
        >
          <Sparkles className="w-5 h-5 animate-pulse" />
          <span>Ask RepoSense AI</span>
        </button>
      )}

      {isOpen && (
        <div className="fixed bottom-6 right-6 w-96 h-[500px] bg-slate-900/95 backdrop-blur-2xl border border-slate-700/80 rounded-2xl shadow-2xl flex flex-col z-50 overflow-hidden">

          {/* Header */}
          <div className="p-4 bg-slate-800/80 border-b border-slate-700/80 flex justify-between items-center">
            <div className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-cyan-400" />
              <span className="font-bold text-sm text-slate-100">
                Repository GraphRAG Chat
              </span>
            </div>

            <button
              onClick={() => setIsOpen(false)}
              className="p-1 hover:bg-slate-700 rounded-lg cursor-pointer"
            >
              <X className="w-5 h-5 text-slate-400" />
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 p-4 overflow-y-auto overflow-x-hidden space-y-3">

            {messages.map((message, index) => (
              <div
                key={index}
                className={`flex gap-2 ${
                  message.sender === 'user'
                    ? 'justify-end'
                    : 'justify-start'
                }`}
              >

                {message.sender === 'ai' && (
                  <Bot className="w-5 h-5 text-cyan-400 shrink-0 mt-1" />
                )}

                <div
                  className={`p-3 rounded-xl text-xs leading-relaxed max-w-[85%] whitespace-pre-wrap break-words ${
                    message.sender === 'user'
                      ? 'bg-purple-600 text-white rounded-br-none'
                      : 'bg-slate-800 border border-slate-700 text-slate-200 rounded-bl-none'
                  }`}
                >
                  {message.text}

                  {/* Confidence */}
                  {message.sender === 'ai' &&
                    message.confidence && (
                      <div className="mt-2 pt-2 border-t border-slate-700 text-[9px] text-cyan-300 uppercase">
                        Confidence: {message.confidence}
                      </div>
                    )}

                  {/* Sources */}
                  {message.sender === 'ai' &&
                    message.sources &&
                    message.sources.length > 0 && (
                      <div className="mt-2 pt-2 border-t border-slate-700">
                        <div className="text-[9px] uppercase font-bold text-slate-400 mb-1">
                          Sources
                        </div>

                        <div className="space-y-1">
                          {message.sources.map(
                            (source, sourceIndex) => (
                              <div
                                key={sourceIndex}
                                className="text-[9px] text-cyan-300 break-all"
                              >
                                {source}
                              </div>
                            ),
                          )}
                        </div>
                      </div>
                    )}
                </div>
              </div>
            ))}

            {/* Loading */}
            {isLoading && (
              <div className="flex gap-2 justify-start">
                <Bot className="w-5 h-5 text-cyan-400 shrink-0 mt-1" />

                <div className="p-3 rounded-xl rounded-bl-none bg-slate-800 border border-slate-700 text-slate-300">
                  <div className="flex items-center gap-2 text-xs">
                    <Loader2 className="w-4 h-4 animate-spin text-cyan-400" />
                    <span>
                      Searching repository knowledge...
                    </span>
                  </div>
                </div>
              </div>
            )}

          </div>

          {/* Preset questions */}
          <div className="p-2 border-t border-slate-800 bg-slate-950/50 flex gap-2 overflow-x-auto [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]">
            {presetQuestions.map((question, index) => (
              <button
                key={index}
                onClick={() => handleSend(question)}
                disabled={isLoading}
                className="whitespace-nowrap px-2.5 py-1 text-[10px] bg-slate-800/80 hover:bg-slate-700 border border-slate-700 text-cyan-300 rounded-full transition cursor-pointer disabled:opacity-50"
              >
                {question}
              </button>
            ))}
          </div>

          {/* Input */}
          <div className="p-3 border-t border-slate-800 flex items-center gap-2 bg-slate-900">

            <input
              type="text"
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter') {
                  handleSend();
                }
              }}
              disabled={isLoading}
              placeholder="Ask a natural language question..."
              className="flex-1 bg-slate-800 border border-slate-700 text-slate-200 text-xs rounded-lg px-3 py-2 outline-none focus:border-cyan-500 disabled:opacity-50"
            />

            <button
              onClick={() => handleSend()}
              disabled={isLoading || !input.trim()}
              className="p-2 bg-cyan-500 hover:bg-cyan-400 text-slate-950 rounded-lg transition disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </button>

          </div>
        </div>
      )}
    </>
  );
};