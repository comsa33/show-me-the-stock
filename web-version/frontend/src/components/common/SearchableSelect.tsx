import React, { useState, useRef, useEffect } from 'react';
import { Search, ChevronDown, X } from 'lucide-react';
import './SearchableSelect.css';

interface Option {
  value: string;
  label: string;
  subLabel?: string;
}

interface SearchableSelectProps {
  options: Option[];
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  loading?: boolean;
  disabled?: boolean;
  className?: string;
}

const SearchableSelect: React.FC<SearchableSelectProps> = ({
  options,
  value,
  onChange,
  placeholder = "선택하세요",
  loading = false,
  disabled = false,
  className = ""
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const filteredOptions = options.filter(option => {
    const searchLower = searchTerm.toLowerCase();
    return option.label.toLowerCase().includes(searchLower) || 
           option.value.toLowerCase().includes(searchLower) ||
           (option.subLabel && option.subLabel.toLowerCase().includes(searchLower));
  });

  const selectedOption = options.find(opt => opt.value === value);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setSearchTerm('');
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
    
    // 모바일에서 드롭다운이 열릴 때 body 스크롤 방지
    if (isOpen && window.innerWidth <= 768) {
      const scrollY = window.scrollY;
      document.body.style.overflow = 'hidden';
      document.body.style.position = 'fixed';
      document.body.style.top = `-${scrollY}px`;
      document.body.style.width = '100%';
      
      return () => {
        document.body.style.overflow = '';
        document.body.style.position = '';
        document.body.style.top = '';
        document.body.style.width = '';
        window.scrollTo(0, scrollY);
      };
    }
  }, [isOpen]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen) {
      if (e.key === 'Enter' || e.key === ' ') {
        setIsOpen(true);
      }
      return;
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setHighlightedIndex(prev => 
          prev < filteredOptions.length - 1 ? prev + 1 : prev
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setHighlightedIndex(prev => prev > 0 ? prev - 1 : -1);
        break;
      case 'Enter':
        e.preventDefault();
        if (highlightedIndex >= 0 && highlightedIndex < filteredOptions.length) {
          handleSelect(filteredOptions[highlightedIndex].value);
        }
        break;
      case 'Escape':
        setIsOpen(false);
        setSearchTerm('');
        break;
    }
  };

  const handleSelect = (selectedValue: string) => {
    onChange(selectedValue);
    setIsOpen(false);
    setSearchTerm('');
    setHighlightedIndex(-1);
  };

  const handleClear = (e: React.MouseEvent) => {
    e.stopPropagation();
    onChange('');
    setSearchTerm('');
  };

  return (
    <div className={`searchable-select ${className}`} ref={dropdownRef}>
      <div 
        className={`select-trigger ${isOpen ? 'open' : ''} ${disabled ? 'disabled' : ''}`}
        onClick={() => !disabled && setIsOpen(!isOpen)}
        tabIndex={disabled ? -1 : 0}
        onKeyDown={handleKeyDown}
      >
        <div className="select-value">
          {selectedOption ? (
            <div className="selected-option">
              <span className="option-label">{selectedOption.label}</span>
              {selectedOption.subLabel && (
                <span className="option-sublabel">{selectedOption.subLabel}</span>
              )}
            </div>
          ) : (
            <span className="placeholder">{placeholder}</span>
          )}
        </div>
        <div className="select-icons">
          {value && !disabled && (
            <X 
              size={16} 
              className="clear-icon" 
              onClick={handleClear}
            />
          )}
          <ChevronDown 
            size={18} 
            className={`dropdown-icon ${isOpen ? 'open' : ''}`} 
          />
        </div>
      </div>

      {isOpen && (
        <>
          {/* 모바일에서만 표시되는 배경 오버레이 */}
          <div 
            className="select-overlay" 
            onClick={() => {
              setIsOpen(false);
              setSearchTerm('');
            }}
          />
          <div className="select-dropdown">
            <div className="dropdown-handle" />
            <div className="search-container">
              <Search size={16} className="search-icon" />
              <input
                ref={inputRef}
                type="text"
                className="search-input"
                placeholder="종목명 또는 코드로 검색..."
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value);
                  setHighlightedIndex(-1);
                }}
                onKeyDown={handleKeyDown}
              />
            </div>

          <div className="options-container">
            {loading ? (
              <div className="loading-message">
                <div className="loading-spinner small"></div>
                <span>종목 로딩 중...</span>
              </div>
            ) : filteredOptions.length === 0 ? (
              <div className="no-results">검색 결과가 없습니다</div>
            ) : (
              filteredOptions.map((option, index) => (
                <div
                  key={option.value}
                  className={`select-option ${
                    option.value === value ? 'selected' : ''
                  } ${index === highlightedIndex ? 'highlighted' : ''}`}
                  onClick={() => handleSelect(option.value)}
                  onMouseEnter={() => setHighlightedIndex(index)}
                >
                  <span className="option-label">{option.label}</span>
                  {option.subLabel && (
                    <span className="option-sublabel">{option.subLabel}</span>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
        </>
      )}
    </div>
  );
};

export default SearchableSelect;