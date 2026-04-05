import React, { useEffect, useRef, useState } from "react";
import { Check, ChevronDown, Eraser, Search, X } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";

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

  const filteredOptions = options.filter((option) => option.toLowerCase().includes(search.toLowerCase()));
  const displayValue =
    selected.length === 0
      ? "Todos"
      : selected.length === 1
        ? selected[0]
        : `${selected.length} selecionados`;

  const toggleOption = (option: string) => {
    if (selected.includes(option)) {
      onChange(selected.filter((value) => value !== option));
      return;
    }

    onChange([...selected, option]);
  };

  const clearSelection = (event: React.MouseEvent) => {
    event.stopPropagation();
    onChange([]);
  };

  const selectAll = () => {
    onChange([]);
  };

  return (
    <div className="relative min-w-[180px] flex-1" ref={dropdownRef}>
      <button
        type="button"
        onClick={() => setIsOpen((value) => !value)}
        className="glass-panel w-full rounded-[24px] px-4 py-3 text-left transition hover:bg-white/80"
      >
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-400">{label}</p>
            <p className="mt-2 truncate text-sm font-semibold text-slate-900">{displayValue}</p>
          </div>

          <div className="flex items-center gap-2">
            {selected.length > 0 ? (
              <span className="rounded-full bg-amber-50 px-2 py-1 text-[10px] font-bold uppercase tracking-[0.16em] text-amber-700">
                {selected.length}
              </span>
            ) : null}
            <ChevronDown
              className="h-4 w-4 flex-shrink-0 text-slate-400 transition-transform"
              style={{ transform: isOpen ? "rotate(180deg)" : "rotate(0deg)" }}
            />
          </div>
        </div>
      </button>

      <AnimatePresence>
        {isOpen ? (
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.98 }}
            transition={{ duration: 0.18, ease: "easeOut" }}
            className="glass-panel absolute left-0 top-[calc(100%+0.5rem)] z-40 w-full overflow-hidden rounded-[26px]"
          >
            <div className="border-b border-slate-200/80 px-4 py-3">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-400">{label}</p>
                  <p className="mt-1 text-sm font-semibold text-slate-900">Ajuste o recorte do painel</p>
                </div>
                <button
                  type="button"
                  onClick={clearSelection}
                  className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-[11px] font-bold uppercase tracking-[0.14em] text-slate-500 transition hover:border-slate-300 hover:text-slate-900"
                >
                  <Eraser className="h-3.5 w-3.5" />
                  Limpar
                </button>
              </div>
            </div>

            <div className="border-b border-slate-200/80 px-4 py-3">
              <div className="flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-3 py-2">
                <Search className="h-4 w-4 text-slate-400" />
                <input
                  type="text"
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Pesquisar opcao"
                  className="w-full bg-transparent text-sm text-slate-700 outline-none placeholder:text-slate-400"
                  onClick={(event) => event.stopPropagation()}
                  autoFocus
                />
                {search ? (
                  <button type="button" onClick={() => setSearch("")} className="text-slate-400 transition hover:text-slate-600">
                    <X className="h-3.5 w-3.5" />
                  </button>
                ) : null}
              </div>

              <button
                type="button"
                onClick={selectAll}
                className="mt-3 inline-flex items-center gap-2 rounded-full bg-slate-950 px-3 py-1.5 text-[11px] font-bold uppercase tracking-[0.14em] text-white transition hover:bg-slate-800"
              >
                Mostrar tudo
              </button>
            </div>

            <div className="max-h-64 overflow-y-auto px-2 py-2">
              {filteredOptions.length === 0 ? (
                <div className="px-4 py-5 text-center text-sm text-slate-400">Nenhum resultado encontrado.</div>
              ) : (
                filteredOptions.map((option) => {
                  const isSelected = selected.includes(option);
                  return (
                    <button
                      key={option}
                      type="button"
                      onClick={() => toggleOption(option)}
                      className="flex w-full items-center gap-3 rounded-2xl px-3 py-2.5 text-left transition hover:bg-white/80"
                    >
                      <span
                        className="flex h-5 w-5 items-center justify-center rounded-full border text-white transition"
                        style={{
                          borderColor: isSelected ? "#0f172a" : "rgba(148, 163, 184, 0.6)",
                          background: isSelected ? "#0f172a" : "transparent",
                        }}
                      >
                        {isSelected ? <Check className="h-3.5 w-3.5" /> : null}
                      </span>
                      <span className="min-w-0 flex-1 truncate text-sm font-medium text-slate-700">{option}</span>
                    </button>
                  );
                })
              )}
            </div>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </div>
  );
}
