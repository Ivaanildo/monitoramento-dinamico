import React, { useState, useRef, useEffect } from "react";
import { ChevronDown, ChevronUp, Search, X, Eraser } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";

interface FilterDropdownProps {
  label: string;
  options: string[];
  selected: string[];
  onChange: (selected: string[]) => void;
}

export function FilterDropdown({ label, options, selected, onChange }: FilterDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState("");
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setSearch("");
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const filtered = options.filter((o) =>
    o.toLowerCase().includes(search.toLowerCase())
  );

  const displayValue = selected.length === 0 ? "Todos" : selected.join(", ");

  const toggleOption = (option: string) => {
    if (selected.includes(option)) {
      onChange(selected.filter((s) => s !== option));
    } else {
      onChange([...selected, option]);
    }
  };

  const clearSelection = (e: React.MouseEvent) => {
    e.stopPropagation();
    onChange([]);
  };

  const selectAll = () => {
    onChange([]);
  };

  return (
    <div className="relative flex-1 min-w-[140px]" ref={dropdownRef}>
      {/* Main Button */}
      <div
        className="rounded-lg overflow-hidden cursor-pointer shadow-md"
        style={{ background: "#FFD700" }}
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="px-3 pt-2 pb-1 flex items-center justify-between">
          <span className="font-bold text-black text-xs tracking-wide">{label}</span>
          {selected.length > 0 && (
            <button
              onClick={clearSelection}
              className="text-black hover:text-gray-600 transition-colors"
            >
              <Eraser size={13} />
            </button>
          )}
        </div>
        <div
          className="px-3 pb-2 flex items-center justify-between gap-1"
          style={{ borderTop: "1px solid rgba(0,0,0,0.12)" }}
        >
          <span className="text-black text-sm truncate max-w-[90%]">{displayValue}</span>
          <ChevronDown
            size={16}
            className="text-black flex-shrink-0 transition-transform duration-200"
            style={{ transform: isOpen ? "rotate(180deg)" : "rotate(0deg)" }}
          />
        </div>
      </div>

      {/* Dropdown Panel */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -8, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.97 }}
            transition={{ duration: 0.18, ease: "easeOut" }}
            className="absolute top-full left-0 z-50 bg-white shadow-2xl rounded-lg mt-1 w-64 border border-gray-200 overflow-hidden"
          >
            {/* Panel Header */}
            <div
              className="px-3 py-2 flex items-center justify-between"
              style={{ background: "#FFD700" }}
            >
              <span className="font-bold text-black text-sm">{label}</span>
              <button onClick={clearSelection} className="text-black hover:text-gray-700 transition-colors">
                <Eraser size={14} />
              </button>
            </div>

            {/* Todos Row */}
            <div
              className="px-3 py-2 flex items-center justify-between cursor-pointer hover:brightness-95 transition-all"
              style={{ background: "#FFD700" }}
              onClick={selectAll}
            >
              <span className="text-black text-sm font-medium">Todos</span>
              <ChevronUp size={16} className="text-black" />
            </div>

            {/* Search */}
            <div className="px-3 py-2 flex items-center gap-2 border-b border-gray-200 bg-white">
              <Search size={14} className="text-gray-400 flex-shrink-0" />
              <input
                type="text"
                placeholder="Pesquisar"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="flex-1 outline-none text-sm text-gray-700 placeholder-gray-400"
                onClick={(e) => e.stopPropagation()}
                autoFocus
              />
              {search && (
                <button onClick={() => setSearch("")} className="text-gray-400 hover:text-gray-600">
                  <X size={12} />
                </button>
              )}
            </div>

            {/* Options List */}
            <div className="max-h-52 overflow-y-auto">
              {filtered.length === 0 ? (
                <div className="px-3 py-3 text-sm text-gray-400 text-center">
                  Nenhum resultado
                </div>
              ) : (
                filtered.map((option) => (
                  <div
                    key={option}
                    className="px-3 py-2 flex items-center gap-2 hover:bg-yellow-50 cursor-pointer transition-colors border-b border-gray-50"
                    onClick={() => toggleOption(option)}
                  >
                    <div
                      className="w-4 h-4 flex-shrink-0 border-2 rounded-sm flex items-center justify-center transition-all"
                      style={{
                        borderColor: selected.includes(option) ? "#FFD700" : "#aaa",
                        background: selected.includes(option) ? "#FFD700" : "white",
                      }}
                    >
                      {selected.includes(option) && (
                        <svg width="10" height="8" viewBox="0 0 10 8" fill="none">
                          <path
                            d="M1 4L3.5 6.5L9 1"
                            stroke="black"
                            strokeWidth="1.8"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          />
                        </svg>
                      )}
                    </div>
                    <span className="text-sm text-gray-800">{option}</span>
                  </div>
                ))
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
