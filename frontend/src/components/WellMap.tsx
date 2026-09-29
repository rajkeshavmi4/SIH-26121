import { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type { Well } from '../api';

type Props = {
  active: Well;
  offsets: Well[];
  radiusKm?: number;
  onRadiusChange?: (radius: number) => void;
};

type MapLayer = 'satellite' | 'dark';

const RADIUS_OPTIONS = [20, 35, 50, 75, 100];

export default function WellMap({ active, offsets, radiusKm = 50, onRadiusChange }: Props) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const layerGroupRef = useRef<L.LayerGroup | null>(null);
  const [mapLayer, setMapLayer] = useState<MapLayer>('satellite');
  const tileLayerRef = useRef<L.TileLayer | null>(null);

  const satelliteUrl = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}';
  const darkUrl = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';

  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current, {
        center: [active.latitude, active.longitude],
        zoom: 10,
        zoomControl: true,
        attributionControl: false,
      });

      const initialTile = L.tileLayer(satelliteUrl, {
        maxZoom: 18,
      }).addTo(map);

      tileLayerRef.current = initialTile;

      const layerGroup = L.layerGroup().addTo(map);
      layerGroupRef.current = layerGroup;
      mapInstanceRef.current = map;
    }

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (!mapInstanceRef.current || !tileLayerRef.current) return;
    const url = mapLayer === 'satellite' ? satelliteUrl : darkUrl;
    tileLayerRef.current.setUrl(url);
  }, [mapLayer]);

  useEffect(() => {
    const map = mapInstanceRef.current;
    const layerGroup = layerGroupRef.current;
    if (!map || !layerGroup) return;

    layerGroup.clearLayers();

    const searchRadiusMeters = radiusKm * 1000;
    const searchRadiusCircle = L.circle([active.latitude, active.longitude], {
      radius: searchRadiusMeters,
      color: '#7ed8a4',
      weight: 1.5,
      dashArray: '4, 8',
      fillColor: '#7ed8a4',
      fillOpacity: 0.05,
    });
    layerGroup.addLayer(searchRadiusCircle);

    const activePulseIcon = L.divIcon({
      className: 'leaflet-active-pulse-wrapper',
      html: '<div class="active-well-pulse"></div><div class="active-well-core"></div>',
      iconSize: [24, 24],
      iconAnchor: [12, 12],
    });

    const activeMarker = L.marker([active.latitude, active.longitude], {
      icon: activePulseIcon,
      zIndexOffset: 1000,
    });

    activeMarker.bindPopup(`
      <div class="leaflet-well-popup">
        <div class="popup-tag active-tag">ACTIVE DRILLING WELL</div>
        <div class="popup-title">${active.name}</div>
        <div class="popup-row"><span>Well ID:</span> <strong>${active.id}</strong></div>
        <div class="popup-row"><span>Formation:</span> <strong>${active.formation}</strong></div>
        <div class="popup-row"><span>Total Depth:</span> <strong>${active.total_depth_m.toLocaleString()} m</strong></div>
        <div class="popup-row"><span>Coordinates:</span> <strong>${active.latitude.toFixed(4)} N, ${active.longitude.toFixed(4)} E</strong></div>
        <div class="popup-row"><span>Trajectory:</span> <strong>${active.trajectory || 'Vertical'}</strong></div>
      </div>
    `);
    layerGroup.addLayer(activeMarker);

    const bounds = searchRadiusCircle.getBounds();

    const topOffsets = offsets.slice(0, 5);
    topOffsets.forEach(w => {
      const line = L.polyline(
        [
          [active.latitude, active.longitude],
          [w.latitude, w.longitude],
        ],
        {
          color: '#f0a35b',
          weight: 1.5,
          opacity: 0.5,
          dashArray: '3, 6',
        }
      );
      layerGroup.addLayer(line);
    });

    offsets.forEach(w => {
      const score = w.relevance_score ?? 50;
      const radius = Math.max(7, Math.min(13, 7 + (score / 100) * 6));

      const marker = L.circleMarker([w.latitude, w.longitude], {
        radius,
        color: '#111e18',
        weight: 1.5,
        fillColor: '#f0a35b',
        fillOpacity: 0.75 + (score / 400),
      });

      marker.bindPopup(`
        <div class="leaflet-well-popup">
          <div class="popup-tag offset-tag">HISTORICAL OFFSET WELL</div>
          <div class="popup-title">${w.name}</div>
          <div class="popup-row"><span>Well ID:</span> <strong>${w.id}</strong></div>
          <div class="popup-row"><span>Relevance Score:</span> <strong style="color: #7ed8a4;">${w.relevance_score ?? 'N/A'}</strong></div>
          <div class="popup-row"><span>Distance:</span> <strong>${w.distance_km != null ? `${w.distance_km} km` : 'N/A'}</strong></div>
          <div class="popup-row"><span>Formation:</span> <strong>${w.formation}</strong></div>
          <div class="popup-row"><span>Total Depth:</span> <strong>${w.total_depth_m.toLocaleString()} m</strong></div>
          <div class="popup-row"><span>Coordinates:</span> <strong>${w.latitude.toFixed(4)} N, ${w.longitude.toFixed(4)} E</strong></div>
        </div>
      `);

      marker.bindTooltip(
        `${w.name} (${w.distance_km != null ? `${w.distance_km} km` : ''} · Score: ${score})`,
        { direction: 'top', className: 'leaflet-well-tooltip', offset: [0, -8] }
      );

      layerGroup.addLayer(marker);
    });

    map.fitBounds(bounds.pad(0.08));
  }, [active, offsets, radiusKm]);

  const handleRecenter = () => {
    if (!mapInstanceRef.current) return;
    mapInstanceRef.current.setView([active.latitude, active.longitude], 10, { animate: true });
  };

  return (
    <div className="panel" style={{ display: 'flex', flexDirection: 'column', height: '100%', minHeight: 460 }}>
      <div className="panel-head" style={{ marginBottom: 10 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <h3>Oil Wells Geospatial Intelligence</h3>
            <span className="badge" style={{ fontSize: 9 }}>WGS84</span>
          </div>
          <p className="sub">Satellite imagery and offset proximity field with user-defined radius</p>
        </div>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
          {onRadiusChange && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 4, background: 'var(--panel2)', border: '1px solid var(--line2)', borderRadius: 6, padding: '2px 6px' }}>
              <span style={{ fontSize: 10, fontFamily: 'DM Mono', color: 'var(--muted)' }}>RADIUS:</span>
              {RADIUS_OPTIONS.map(r => (
                <button
                  key={r}
                  type="button"
                  onClick={() => onRadiusChange(r)}
                  style={{
                    background: radiusKm === r ? 'var(--mint)' : 'transparent',
                    color: radiusKm === r ? '#0a1a10' : 'var(--muted)',
                    border: 'none',
                    borderRadius: 4,
                    padding: '2px 6px',
                    fontSize: 10,
                    fontFamily: 'DM Mono',
                    fontWeight: radiusKm === r ? 700 : 400,
                  }}
                >
                  {r}km
                </button>
              ))}
            </div>
          )}
          <div className="map-view-switcher">
            <button
              type="button"
              className={`map-switch-btn ${mapLayer === 'satellite' ? 'active' : ''}`}
              onClick={() => setMapLayer('satellite')}
            >
              Satellite
            </button>
            <button
              type="button"
              className={`map-switch-btn ${mapLayer === 'dark' ? 'active' : ''}`}
              onClick={() => setMapLayer('dark')}
            >
              Dark Field
            </button>
          </div>
          <button
            type="button"
            className="action"
            style={{ padding: '4px 8px', fontSize: 11 }}
            onClick={handleRecenter}
            title="Recenter on Active Well"
          >
            Recenter
          </button>
        </div>
      </div>

      <div
        ref={mapContainerRef}
        style={{
          flex: 1,
          minHeight: 360,
          borderRadius: 8,
          overflow: 'hidden',
          border: '1px solid var(--line)',
          position: 'relative',
        }}
      />

      <div className="map-legend" style={{ marginTop: 10, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
        <div style={{ display: 'flex', gap: 14, alignItems: 'center', flexWrap: 'wrap' }}>
          <div className="legend-item">
            <div className="legend-dot" style={{ background: 'var(--mint)', boxShadow: '0 0 6px var(--mint)' }} />
            Active Well: {active.name.replace('NWIS Demo ', '')}
          </div>
          <div className="legend-item">
            <div className="legend-dot" style={{ background: 'var(--orange)' }} />
            Historical Offsets ({offsets.length})
          </div>
          <div className="legend-item">
            <div className="legend-dot" style={{ background: 'transparent', border: '1px dashed var(--mint)', width: 10, height: 10 }} />
            {radiusKm} km Search Corridor
          </div>
        </div>
        <div style={{ fontFamily: 'DM Mono', fontSize: 10, color: 'var(--muted)' }}>
          {active.latitude.toFixed(4)} N, {active.longitude.toFixed(4)} E
        </div>
      </div>
    </div>
  );
}
