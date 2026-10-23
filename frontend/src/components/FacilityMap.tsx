import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { FacilityReadiness, Lang } from '../types';
import { makeT } from '../i18n';

interface FacilityMapProps {
  facilities: FacilityReadiness[];
  selectedId: number | null;
  onSelect: (facilityId: number) => void;
  language: Lang;
}

const TYPE_COLOR: Record<string, string> = {
  PHC: '#0d9488',
  CHC: '#2563eb',
  SUB_DISTRICT: '#7c3aed',
  DISTRICT_HOSPITAL: '#dc2626',
};

export const FacilityMap: React.FC<FacilityMapProps> = ({ facilities, selectedId, onSelect, language }) => {
  const t = makeT(language);
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const layerRef = useRef<L.LayerGroup | null>(null);
  const [tilesFailed, setTilesFailed] = useState(false);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const map = L.map(containerRef.current, { scrollWheelZoom: false });
    const tiles = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18,
      attribution: '&copy; OpenStreetMap contributors',
    });
    tiles.on('tileerror', () => setTilesFailed(true));
    tiles.addTo(map);
    layerRef.current = L.layerGroup().addTo(map);
    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    const layer = layerRef.current;
    if (!map || !layer) return;
    layer.clearLayers();
    const points: L.LatLngExpression[] = [];
    facilities.forEach(f => {
      const pos: L.LatLngExpression = [f.latitude, f.longitude];
      points.push(pos);
      const marker = L.circleMarker(pos, {
        radius: f.id === selectedId ? 11 : 8,
        color: '#ffffff',
        weight: 2,
        fillColor: TYPE_COLOR[f.facility_type] || '#475569',
        fillOpacity: 0.95,
      });
      marker.bindTooltip(
        `<strong>${f.name}</strong><br/>${f.facility_type} • ${f.distance_km} km • ${f.available_doctors_count} ${t('डॉक्टर ड्यूटी पर', 'doctors on duty')}`,
        { direction: 'top' }
      );
      marker.on('click', () => onSelect(f.id));
      marker.addTo(layer);
    });
    if (points.length === 1) map.setView(points[0], 12);
    else if (points.length > 1) map.fitBounds(L.latLngBounds(points), { padding: [45, 45] });
  }, [facilities, selectedId, language]);

  return (
    <div className="space-y-2">
      <div ref={containerRef} className="h-72 w-full rounded-xl border border-slate-200 z-0" role="region" aria-label={t('नक्शा', 'Map')} />
      <div className="flex flex-wrap items-center gap-3 text-[11px] text-slate-600">
        {Object.entries(TYPE_COLOR).filter(([type]) => facilities.some(f => f.facility_type === type)).map(([type, color]) => (
          <span key={type} className="flex items-center gap-1"><span className="inline-block w-3 h-3 rounded-full" style={{ background: color }} />{type.replace('_', ' ')}</span>
        ))}
        <span className="text-slate-400">{tilesFailed ? t('नक्शा उपलब्ध नहीं (इंटरनेट नहीं)।', 'Map unavailable (no internet for map tiles).') : t('बुकिंग के लिए किसी निशान पर टैप करें।', 'Tap a marker to choose that facility for booking.')}</span>
      </div>
    </div>
  );
};
