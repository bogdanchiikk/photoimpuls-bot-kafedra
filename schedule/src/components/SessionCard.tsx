import { ScheduleEvent } from "../data/schedule";

interface SessionCardProps {
  data: ScheduleEvent;
}

export function SessionCard({ data }: SessionCardProps) {
  return (
    <div className={`bg-white rounded-lg shadow-md p-6 border-l-4 border-yellow-400 ${data.cell_id === 'D1_1200_H5' ? 'ring-4 ring-yellow-400' : ''}`}>
      <div className="mb-2">
        <span className="text-xs font-semibold text-gray-500 uppercase">
          {data.event_type}
        </span>
      </div>
      <h3 className="text-lg font-bold mb-2">{data.title}</h3>
      <p className="text-sm text-gray-600 mb-2">
        <strong>Зал:</strong> {data.hall}
      </p>
      {data.chair_name && (
        <p className="text-sm text-gray-600 mb-2">
          <strong>Модератор:</strong> {data.chair_name}
        </p>
      )}
      {data.speakers && (
        <p className="text-sm text-gray-700 mb-2">
          <strong>Спикеры:</strong> {data.speakers}
        </p>
      )}
      {data.notes && (
        <p className="text-xs text-gray-500 italic mt-2">{data.notes}</p>
      )}
    </div>
  );
}
