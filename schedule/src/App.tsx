import { useState, useMemo } from "react";
import { SessionCard } from "./components/SessionCard";
import { scheduleData, ScheduleEvent } from "./data/schedule";

// Grouping utility
const groupEvents = (events: ScheduleEvent[]) => {
  const byDay: Record<string, Record<string, ScheduleEvent[]>> = {};

  events.forEach((event) => {
    if (!byDay[event.day_label]) {
      byDay[event.day_label] = {};
    }
    if (!byDay[event.day_label][event.time_slot]) {
      byDay[event.day_label][event.time_slot] = [];
    }
    byDay[event.day_label][event.time_slot].push(event);
  });

  return byDay;
};

// Get unique halls and speakers from events
const getUniqueHalls = (events: ScheduleEvent[]): string[] => {
  const halls = new Set(events.map(e => e.hall));
  return Array.from(halls).sort();
};

const getUniqueSpeakers = (events: ScheduleEvent[]): string[] => {
  const speakers = new Set<string>();
  
  events.forEach(event => {
    if (!event.speakers) return;
    
    // Разбиваем по точке с пробелом (разделитель между именами)
    // Также учитываем случаи, где точка может быть частью инициалов
    const parts = event.speakers.split(/\.\s+/);
    
    parts.forEach(part => {
      let speaker = part.trim();
      if (!speaker) return;
      
      // Убираем текст после двоеточия (названия докладов)
      const colonIndex = speaker.indexOf(':');
      if (colonIndex > 0) {
        speaker = speaker.substring(0, colonIndex).trim();
      }
      
      // Убираем текст в скобках (дополнительная информация)
      speaker = speaker.replace(/\([^)]*\)/g, '').trim();
      
      // Убираем лишние пробелы
      speaker = speaker.replace(/\s+/g, ' ').trim();
      
      // Проверяем, что это похоже на имя (содержит буквы, не слишком короткое)
      // Имя обычно содержит хотя бы одну заглавную букву и точку (инициалы) или несколько слов
      if (speaker.length < 3) return; // Слишком короткое
      if (speaker.length > 100) return; // Слишком длинное (вероятно, не имя)
      
      // Проверяем, что содержит хотя бы одну русскую или латинскую букву
      if (!/[\u0400-\u04FFa-zA-Z]/.test(speaker)) return;
      
      // Фильтруем явно не-имена (начинаются с маленькой буквы и длинные - вероятно, текст доклада)
      if (speaker.length > 30 && /^[а-яa-z]/.test(speaker)) return;
      
      // Фильтруем строки, которые выглядят как названия докладов (содержат много пробелов и длинные)
      const words = speaker.split(/\s+/);
      if (words.length > 5) return; // Слишком много слов - вероятно, не имя
      
      // Добавляем только если похоже на имя (содержит точку с инициалами или 2-3 слова)
      const hasInitials = /\./.test(speaker); // Есть точка (инициалы)
      const hasProperName = words.length >= 2 && words.length <= 4; // 2-4 слова
      
      if (hasInitials || hasProperName) {
        speakers.add(speaker);
      }
    });
  });
  
  return Array.from(speakers).sort();
};

export default function App() {
  const groupedData = groupEvents(scheduleData);
  const days = Object.keys(groupedData);
  const [activeDay, setActiveDay] = useState(days[0]);
  const [selectedHall, setSelectedHall] = useState<string | null>(null);
  const [selectedSpeaker, setSelectedSpeaker] = useState<string | null>(null);
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  // Get all events for the active day
  const dayEvents = useMemo(() => {
    const events: ScheduleEvent[] = [];
    Object.values(groupedData[activeDay] || {}).forEach(timeSlotEvents => {
      events.push(...timeSlotEvents);
    });
    return events;
  }, [activeDay, groupedData]);

  // Get unique halls and speakers for the active day
  const halls = useMemo(() => getUniqueHalls(dayEvents), [dayEvents]);
  const speakers = useMemo(() => getUniqueSpeakers(dayEvents), [dayEvents]);

  // Filter events based on selected hall and speaker
  const filteredGroupedData = useMemo(() => {
    const filtered: Record<string, ScheduleEvent[]> = {};
    
    Object.entries(groupedData[activeDay] || {}).forEach(([timeSlot, events]) => {
      const filteredEvents = events.filter(event => {
        const matchesHall = !selectedHall || event.hall === selectedHall;
        
        // Более точная проверка спикера
        let matchesSpeaker = true;
        if (selectedSpeaker && event.speakers) {
          // Нормализуем строку спикеров для поиска
          const speakersText = event.speakers.toLowerCase();
          const searchName = selectedSpeaker.toLowerCase();
          
          // Ищем точное совпадение имени (с учетом того, что имя может быть частью строки)
          // Проверяем, что имя встречается как отдельное слово или в начале строки
          const namePattern = new RegExp(
            `(^|\\s|\\.)${searchName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}(\\s|\\.|:|$)`,
            'i'
          );
          matchesSpeaker = namePattern.test(speakersText);
        }
        
        return matchesHall && matchesSpeaker;
      });
      
      if (filteredEvents.length > 0) {
        filtered[timeSlot] = filteredEvents;
      }
    });
    
    return filtered;
  }, [activeDay, groupedData, selectedHall, selectedSpeaker]);

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold">Вейновские чтения</h1>
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="px-4 py-2 bg-yellow-400 text-black font-semibold rounded hover:bg-yellow-500 transition-colors"
            >
              {isMenuOpen ? '✕ Закрыть фильтры' : '☰ Фильтры'}
            </button>
          </div>
        </div>
      </header>

      {/* Filters Panel */}
      {isMenuOpen && (
        <div className="bg-white border-b border-gray-200 shadow-md">
          <div className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Hall Filter */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Фильтр по залам:
                </label>
                <select
                  value={selectedHall || ''}
                  onChange={(e) => setSelectedHall(e.target.value || null)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-yellow-400"
                >
                  <option value="">Все залы</option>
                  {halls.map((hall) => (
                    <option key={hall} value={hall}>
                      {hall}
                    </option>
                  ))}
                </select>
              </div>

              {/* Speaker Filter */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Фильтр по спикерам:
                </label>
                <select
                  value={selectedSpeaker || ''}
                  onChange={(e) => setSelectedSpeaker(e.target.value || null)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-yellow-400"
                >
                  <option value="">Все спикеры</option>
                  {speakers.map((speaker) => (
                    <option key={speaker} value={speaker}>
                      {speaker}
                    </option>
                  ))}
                </select>
              </div>
            </div>
            
            {/* Clear Filters Button */}
            {(selectedHall || selectedSpeaker) && (
              <div className="mt-4">
                <button
                  onClick={() => {
                    setSelectedHall(null);
                    setSelectedSpeaker(null);
                  }}
                  className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors"
                >
                  Сбросить фильтры
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      <main className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Day Tabs */}
        <div className="flex gap-2 mb-8 border-b border-gray-200">
          {days.map((day) => (
            <button
              key={day}
              onClick={() => {
                setActiveDay(day);
                setSelectedHall(null);
                setSelectedSpeaker(null);
              }}
              className={`px-6 py-3 rounded-none text-sm font-bold uppercase tracking-wider transition-all duration-200 border-b-4 ${
                activeDay === day
                  ? 'border-yellow-400 text-black bg-yellow-50'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              {day}
            </button>
          ))}
        </div>

        {/* Events */}
        <div className="space-y-16">
          {Object.keys(filteredGroupedData).length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500 text-lg">
                {selectedHall || selectedSpeaker 
                  ? 'Нет событий, соответствующих выбранным фильтрам'
                  : 'Нет событий на этот день'}
              </p>
            </div>
          ) : (
            Object.entries(filteredGroupedData).map(([timeSlot, events]) => (
              <div key={timeSlot}>
                <h2 className="text-xl font-bold mb-4">{timeSlot}</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {events.map((event) => (
                    <SessionCard key={event.cell_id} data={event} />
                  ))}
                </div>
              </div>
            ))
          )}
        </div>
      </main>

      <footer className="mt-20 py-10 border-t border-gray-200 bg-white text-center text-gray-600">
        <p className="mb-4 text-base">Создано агентством Кафедра</p>
        <a href="https://kafedra.agency" target="_blank" rel="noopener noreferrer">
          <img src="/kafedra-logo.png" alt="Кафедра" className="h-24 w-auto mx-auto object-contain" />
        </a>
      </footer>
    </div>
  );
}
