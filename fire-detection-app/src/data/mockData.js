const locations = [
    { name: 'Jamshedpur Steel Belt', lat: 22.8046, lng: 86.2029, type: 'Industrial Heat Source' },
    { name: 'Paradip Refinery', lat: 20.3167, lng: 86.6167, type: 'Industrial Heat Source' },
    { name: 'Angul Industrial Zone', lat: 20.8400, lng: 85.1000, type: 'Persistent Thermal Anomaly' },
    { name: 'Bokaro Steel City', lat: 23.6693, lng: 86.1511, type: 'Industrial Heat Source' },
    { name: 'Jamnagar Refinery Complex', lat: 22.2394, lng: 70.0119, type: 'Persistent Thermal Anomaly' },
    { name: 'Rourkela Steel Plant', lat: 22.2604, lng: 84.8536, type: 'Industrial Heat Source' },
    { name: 'Bastar Forest Belt', lat: 19.1071, lng: 81.9550, type: 'Vegetation Fire' },
    { name: 'Similipal Reserve', lat: 21.6167, lng: 86.2333, type: 'Vegetation Fire' },
    { name: 'Nagarhole Forest', lat: 12.0000, lng: 76.1333, type: 'Vegetation Fire' },
    { name: 'Barmer Gas Field', lat: 25.7521, lng: 71.3967, type: 'Persistent Thermal Anomaly' },
    { name: 'Raigad MIDC', lat: 18.5158, lng: 73.1822, type: 'Industrial Heat Source' },
    { name: 'Vizag Steel Plant', lat: 17.6868, lng: 83.2185, type: 'Industrial Heat Source' },
    { name: 'Bandhavgarh Buffer Zone', lat: 23.6900, lng: 81.0000, type: 'Vegetation Fire' },
    { name: 'Durgapur Industrial Area', lat: 23.5204, lng: 87.3119, type: 'Persistent Thermal Anomaly' },
  ];
  
  const satellites = ['VIIRS-NOAA20', 'VIIRS-SNPP', 'MODIS-Aqua', 'MODIS-Terra'];
  
  function rand(min, max) { return Math.round((Math.random() * (max - min) + min) * 10) / 10; }
  
  export const detections = locations.map((loc, i) => ({
    id: i + 1,
    location: loc.name,
    lat: loc.lat + rand(-0.05, 0.05),
    lng: loc.lng + rand(-0.05, 0.05),
    classification: loc.type,
    confidence: Math.round(rand(65, 98)),
    brightness: Math.round(rand(300, 480)),
    frp: rand(5, 90),
    satellite: satellites[i % satellites.length],
    time: `${Math.round(rand(2, 180))}m ago`,
  }));