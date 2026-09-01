/*
 * Nairobi Wild — the atlas
 *
 * The campaign is a tour of the whole continent: every African country,
 * and within each one its major cities as stages that get harder as you
 * work through them. Finish a country and the next one unlocks.
 *
 * Each country fields ITS OWN six animals — the creatures that country is
 * actually known for. Kenya plays with the Big Five plus a giraffe; Uganda
 * swaps in gorillas and hippos; Madagascar plays lemurs and chameleons;
 * Mauritius fields the dodo. That is what stops 250 stages of the same
 * mechanic feeling like one long level.
 *
 * The board always has six colour slots with fixed hues, and a country
 * simply maps its animals onto those slots. Colour identity therefore
 * never depends on which animals are in play, which keeps the board
 * readable for colour-blind players wherever you are on the map.
 *
 * Everything here is DATA. Adding a city is one string; adding a country
 * is one row. The difficulty curve is generated, so it cannot drift.
 */
(function (global) {
  'use strict';

  /*
   * The animal pool. `voice` names an archetype in sounds.js — many
   * species share a manner of calling, and a warthog snorts much like a
   * rhino does.
   */
  const ANIMALS = {
    lion:      { g: '🦁', en: 'Lion',       voice: 'roar' },
    elephant:  { g: '🐘', en: 'Elephant',   voice: 'trumpet' },
    rhino:     { g: '🦏', en: 'Rhino',      voice: 'snort' },
    leopard:   { g: '🐆', en: 'Leopard',    voice: 'rasp' },
    buffalo:   { g: '🐃', en: 'Buffalo',    voice: 'bellow' },
    giraffe:   { g: '🦒', en: 'Giraffe',    voice: 'hum' },
    zebra:     { g: '🦓', en: 'Zebra',      voice: 'bark' },
    hippo:     { g: '🦛', en: 'Hippo',      voice: 'grunt' },
    gorilla:   { g: '🦍', en: 'Gorilla',    voice: 'hoot' },
    monkey:    { g: '🐒', en: 'Monkey',     voice: 'chatter' },
    crocodile: { g: '🐊', en: 'Crocodile',  voice: 'hiss' },
    hyena:     { g: '🐕', en: 'Hyena',      voice: 'whoop' },
    camel:     { g: '🐪', en: 'Camel',      voice: 'bleat' },
    antelope:  { g: '🦌', en: 'Antelope',   voice: 'bleat' },
    warthog:   { g: '🐗', en: 'Warthog',    voice: 'snort' },
    flamingo:  { g: '🦩', en: 'Flamingo',   voice: 'honk' },
    eagle:     { g: '🦅', en: 'Eagle',      voice: 'screech' },
    parrot:    { g: '🦜', en: 'Parrot',     voice: 'squawk' },
    penguin:   { g: '🐧', en: 'Penguin',    voice: 'bray' },
    seal:      { g: '🦭', en: 'Seal',       voice: 'bray' },
    fox:       { g: '🦊', en: 'Fennec Fox', voice: 'yelp' },
    snake:     { g: '🐍', en: 'Cobra',      voice: 'hiss' },
    goat:      { g: '🐐', en: 'Mountain Goat', voice: 'bleat' },
    chameleon: { g: '🦎', en: 'Chameleon',  voice: 'hiss' },
    turtle:    { g: '🐢', en: 'Turtle',     voice: 'splash' },
    bat:       { g: '🦇', en: 'Fruit Bat',  voice: 'chatter' },
    fish:      { g: '🐟', en: 'Fish',       voice: 'splash' },
    dolphin:   { g: '🐬', en: 'Dolphin',    voice: 'splash' },
    shark:     { g: '🦈', en: 'Shark',      voice: 'splash' },
    crab:      { g: '🦀', en: 'Crab',       voice: 'splash' },
    dodo:      { g: '🦤', en: 'Dodo',       voice: 'honk' },
    owl:       { g: '🦉', en: 'Owl',        voice: 'screech' },
  };

  /*
   * The tour. It begins in Nairobi, because that is where the game is
   * made, then works outward through East Africa, the Horn, Southern,
   * Central, West, North Africa and the islands.
   *
   * `animals` are that country's six, in board-colour order.
   */
  const COUNTRIES = [
    // ---- East Africa ----
    { name: 'Kenya', flag: '🇰🇪', region: 'East Africa',
      animals: ['lion', 'elephant', 'zebra', 'giraffe', 'rhino', 'leopard'],
      cities: ['Nairobi', 'Mombasa', 'Kisumu', 'Nakuru', 'Eldoret', 'Malindi'] },
    { name: 'Tanzania', flag: '🇹🇿', region: 'East Africa',
      animals: ['lion', 'elephant', 'zebra', 'giraffe', 'hippo', 'leopard'],
      cities: ['Dar es Salaam', 'Dodoma', 'Arusha', 'Mwanza', 'Zanzibar City', 'Mbeya'] },
    { name: 'Uganda', flag: '🇺🇬', region: 'East Africa',
      animals: ['gorilla', 'elephant', 'buffalo', 'crocodile', 'hippo', 'monkey'],
      cities: ['Kampala', 'Entebbe', 'Jinja', 'Gulu', 'Mbarara'] },
    { name: 'Rwanda', flag: '🇷🇼', region: 'East Africa',
      animals: ['gorilla', 'elephant', 'buffalo', 'antelope', 'leopard', 'monkey'],
      cities: ['Kigali', 'Butare', 'Gisenyi', 'Musanze'] },
    { name: 'Burundi', flag: '🇧🇮', region: 'East Africa',
      animals: ['hippo', 'elephant', 'buffalo', 'antelope', 'crocodile', 'monkey'],
      cities: ['Gitega', 'Bujumbura', 'Ngozi', 'Rumonge'] },
    // ---- Horn of Africa ----
    { name: 'Ethiopia', flag: '🇪🇹', region: 'Horn of Africa',
      animals: ['monkey', 'fox', 'goat', 'hyena', 'eagle', 'antelope'],
      cities: ['Addis Ababa', 'Dire Dawa', 'Gondar', 'Bahir Dar', 'Mekelle', 'Hawassa'] },
    { name: 'Eritrea', flag: '🇪🇷', region: 'Horn of Africa',
      animals: ['camel', 'antelope', 'goat', 'eagle', 'monkey', 'fish'],
      cities: ['Asmara', 'Keren', 'Massawa', 'Assab'] },
    { name: 'Djibouti', flag: '🇩🇯', region: 'Horn of Africa',
      animals: ['camel', 'antelope', 'flamingo', 'eagle', 'goat', 'fish'],
      cities: ['Djibouti City', 'Ali Sabieh', 'Tadjoura', 'Obock'] },
    { name: 'Somalia', flag: '🇸🇴', region: 'Horn of Africa',
      animals: ['camel', 'leopard', 'antelope', 'hyena', 'eagle', 'fish'],
      cities: ['Mogadishu', 'Hargeisa', 'Bosaso', 'Kismayo', 'Berbera'] },
    // ---- Southern Africa ----
    { name: 'Zambia', flag: '🇿🇲', region: 'Southern Africa',
      animals: ['elephant', 'hippo', 'buffalo', 'antelope', 'crocodile', 'leopard'],
      cities: ['Lusaka', 'Kitwe', 'Ndola', 'Livingstone', 'Kabwe'] },
    { name: 'Zimbabwe', flag: '🇿🇼', region: 'Southern Africa',
      animals: ['lion', 'elephant', 'buffalo', 'eagle', 'rhino', 'hippo'],
      cities: ['Harare', 'Bulawayo', 'Mutare', 'Gweru', 'Victoria Falls'] },
    { name: 'Malawi', flag: '🇲🇼', region: 'Southern Africa',
      animals: ['hippo', 'elephant', 'fish', 'antelope', 'crocodile', 'eagle'],
      cities: ['Lilongwe', 'Blantyre', 'Mzuzu', 'Zomba'] },
    { name: 'Mozambique', flag: '🇲🇿', region: 'Southern Africa',
      animals: ['elephant', 'hippo', 'dolphin', 'antelope', 'crocodile', 'buffalo'],
      cities: ['Maputo', 'Matola', 'Beira', 'Nampula', 'Pemba'] },
    { name: 'Botswana', flag: '🇧🇼', region: 'Southern Africa',
      animals: ['lion', 'elephant', 'zebra', 'antelope', 'hippo', 'eagle'],
      cities: ['Gaborone', 'Francistown', 'Maun', 'Kasane'] },
    { name: 'Namibia', flag: '🇳🇦', region: 'Southern Africa',
      animals: ['antelope', 'elephant', 'zebra', 'seal', 'rhino', 'leopard'],
      cities: ['Windhoek', 'Walvis Bay', 'Swakopmund', 'Oshakati', 'Rundu'] },
    { name: 'South Africa', flag: '🇿🇦', region: 'Southern Africa',
      animals: ['lion', 'elephant', 'penguin', 'buffalo', 'rhino', 'leopard'],
      cities: ['Johannesburg', 'Cape Town', 'Durban', 'Pretoria', 'Gqeberha', 'Bloemfontein'] },
    { name: 'Lesotho', flag: '🇱🇸', region: 'Southern Africa',
      animals: ['goat', 'antelope', 'monkey', 'eagle', 'snake', 'fox'],
      cities: ['Maseru', 'Teyateyaneng', 'Mafeteng', 'Leribe'] },
    { name: 'Eswatini', flag: '🇸🇿', region: 'Southern Africa',
      animals: ['lion', 'elephant', 'antelope', 'hippo', 'rhino', 'crocodile'],
      cities: ['Mbabane', 'Manzini', 'Lobamba', 'Siteki'] },
    { name: 'Angola', flag: '🇦🇴', region: 'Southern Africa',
      animals: ['lion', 'elephant', 'antelope', 'buffalo', 'hippo', 'crocodile'],
      cities: ['Luanda', 'Huambo', 'Lobito', 'Benguela', 'Lubango'] },
    // ---- Central Africa ----
    { name: 'DR Congo', flag: '🇨🇩', region: 'Central Africa',
      animals: ['gorilla', 'elephant', 'parrot', 'monkey', 'hippo', 'crocodile'],
      cities: ['Kinshasa', 'Lubumbashi', 'Mbuji-Mayi', 'Kisangani', 'Goma', 'Bukavu'] },
    { name: 'Republic of the Congo', flag: '🇨🇬', region: 'Central Africa',
      animals: ['gorilla', 'elephant', 'parrot', 'buffalo', 'hippo', 'monkey'],
      cities: ['Brazzaville', 'Pointe-Noire', 'Dolisie', 'Owando'] },
    { name: 'Cameroon', flag: '🇨🇲', region: 'Central Africa',
      animals: ['gorilla', 'elephant', 'parrot', 'lion', 'hippo', 'monkey'],
      cities: ['Douala', 'Yaoundé', 'Bamenda', 'Garoua', 'Bafoussam'] },
    { name: 'Gabon', flag: '🇬🇦', region: 'Central Africa',
      animals: ['gorilla', 'elephant', 'parrot', 'turtle', 'hippo', 'crocodile'],
      cities: ['Libreville', 'Port-Gentil', 'Franceville', 'Oyem'] },
    { name: 'Central African Republic', flag: '🇨🇫', region: 'Central Africa',
      animals: ['gorilla', 'elephant', 'antelope', 'buffalo', 'crocodile', 'monkey'],
      cities: ['Bangui', 'Bimbo', 'Berbérati', 'Carnot'] },
    { name: 'Chad', flag: '🇹🇩', region: 'Central Africa',
      animals: ['camel', 'elephant', 'antelope', 'eagle', 'hippo', 'crocodile'],
      cities: ["N'Djamena", 'Moundou', 'Sarh', 'Abéché'] },
    { name: 'Equatorial Guinea', flag: '🇬🇶', region: 'Central Africa',
      animals: ['monkey', 'turtle', 'parrot', 'antelope', 'fish', 'crocodile'],
      cities: ['Malabo', 'Bata', 'Ebebiyín', 'Mongomo'] },
    { name: 'São Tomé and Príncipe', flag: '🇸🇹', region: 'Central Africa',
      animals: ['parrot', 'turtle', 'dolphin', 'monkey', 'fish', 'crab'],
      cities: ['São Tomé', 'Trindade', 'Santo António'] },
    // ---- West Africa ----
    { name: 'Nigeria', flag: '🇳🇬', region: 'West Africa',
      animals: ['elephant', 'gorilla', 'parrot', 'monkey', 'hippo', 'crocodile'],
      cities: ['Lagos', 'Abuja', 'Kano', 'Ibadan', 'Port Harcourt', 'Benin City'] },
    { name: 'Ghana', flag: '🇬🇭', region: 'West Africa',
      animals: ['elephant', 'antelope', 'parrot', 'monkey', 'hippo', 'crocodile'],
      cities: ['Accra', 'Kumasi', 'Tamale', 'Takoradi', 'Cape Coast'] },
    { name: "Côte d'Ivoire", flag: '🇨🇮', region: 'West Africa',
      animals: ['elephant', 'antelope', 'parrot', 'monkey', 'hippo', 'crocodile'],
      cities: ['Abidjan', 'Yamoussoukro', 'Bouaké', 'Daloa', 'San-Pédro'] },
    { name: 'Senegal', flag: '🇸🇳', region: 'West Africa',
      animals: ['lion', 'warthog', 'flamingo', 'monkey', 'hippo', 'crocodile'],
      cities: ['Dakar', 'Touba', 'Thiès', 'Saint-Louis', 'Ziguinchor'] },
    { name: 'Mali', flag: '🇲🇱', region: 'West Africa',
      animals: ['elephant', 'camel', 'antelope', 'eagle', 'hippo', 'crocodile'],
      cities: ['Bamako', 'Sikasso', 'Mopti', 'Timbuktu', 'Gao'] },
    { name: 'Burkina Faso', flag: '🇧🇫', region: 'West Africa',
      animals: ['elephant', 'warthog', 'antelope', 'buffalo', 'monkey', 'crocodile'],
      cities: ['Ouagadougou', 'Bobo-Dioulasso', 'Koudougou', 'Banfora'] },
    { name: 'Niger', flag: '🇳🇪', region: 'West Africa',
      animals: ['elephant', 'camel', 'antelope', 'giraffe', 'fox', 'crocodile'],
      cities: ['Niamey', 'Zinder', 'Maradi', 'Agadez', 'Tahoua'] },
    { name: 'Guinea', flag: '🇬🇳', region: 'West Africa',
      animals: ['elephant', 'antelope', 'parrot', 'monkey', 'hippo', 'crocodile'],
      cities: ['Conakry', 'Nzérékoré', 'Kankan', 'Kindia'] },
    { name: 'Sierra Leone', flag: '🇸🇱', region: 'West Africa',
      animals: ['elephant', 'antelope', 'parrot', 'monkey', 'hippo', 'crocodile'],
      cities: ['Freetown', 'Bo', 'Kenema', 'Makeni'] },
    { name: 'Liberia', flag: '🇱🇷', region: 'West Africa',
      animals: ['elephant', 'antelope', 'parrot', 'monkey', 'hippo', 'crocodile'],
      cities: ['Monrovia', 'Gbarnga', 'Buchanan', 'Harper'] },
    { name: 'Togo', flag: '🇹🇬', region: 'West Africa',
      animals: ['elephant', 'antelope', 'parrot', 'buffalo', 'monkey', 'crocodile'],
      cities: ['Lomé', 'Sokodé', 'Kara', 'Kpalimé'] },
    { name: 'Benin', flag: '🇧🇯', region: 'West Africa',
      animals: ['lion', 'elephant', 'antelope', 'buffalo', 'hippo', 'monkey'],
      cities: ['Cotonou', 'Porto-Novo', 'Parakou', 'Abomey'] },
    { name: 'The Gambia', flag: '🇬🇲', region: 'West Africa',
      animals: ['hippo', 'antelope', 'parrot', 'monkey', 'eagle', 'crocodile'],
      cities: ['Banjul', 'Serekunda', 'Brikama', 'Farafenni'] },
    { name: 'Guinea-Bissau', flag: '🇬🇼', region: 'West Africa',
      animals: ['hippo', 'antelope', 'parrot', 'monkey', 'turtle', 'crocodile'],
      cities: ['Bissau', 'Bafatá', 'Gabú', 'Bissorã'] },
    { name: 'Mauritania', flag: '🇲🇷', region: 'West Africa',
      animals: ['camel', 'antelope', 'seal', 'eagle', 'snake', 'fox'],
      cities: ['Nouakchott', 'Nouadhibou', 'Kiffa', 'Rosso'] },
    { name: 'Cape Verde', flag: '🇨🇻', region: 'West Africa',
      animals: ['turtle', 'dolphin', 'seal', 'eagle', 'fish', 'crab'],
      cities: ['Praia', 'Mindelo', 'Santa Maria', 'Assomada'] },
    // ---- North Africa ----
    { name: 'Egypt', flag: '🇪🇬', region: 'North Africa',
      animals: ['camel', 'crocodile', 'fox', 'eagle', 'snake', 'fish'],
      cities: ['Cairo', 'Alexandria', 'Giza', 'Luxor', 'Aswan', 'Port Said'] },
    { name: 'Sudan', flag: '🇸🇩', region: 'North Africa',
      animals: ['camel', 'crocodile', 'antelope', 'eagle', 'hippo', 'monkey'],
      cities: ['Khartoum', 'Omdurman', 'Port Sudan', 'Kassala', 'Nyala'] },
    { name: 'South Sudan', flag: '🇸🇸', region: 'North Africa',
      animals: ['elephant', 'antelope', 'giraffe', 'buffalo', 'hippo', 'crocodile'],
      cities: ['Juba', 'Wau', 'Malakal', 'Yei'] },
    { name: 'Libya', flag: '🇱🇾', region: 'North Africa',
      animals: ['camel', 'antelope', 'fox', 'eagle', 'snake', 'goat'],
      cities: ['Tripoli', 'Benghazi', 'Misrata', 'Sabha'] },
    { name: 'Tunisia', flag: '🇹🇳', region: 'North Africa',
      animals: ['camel', 'flamingo', 'fox', 'eagle', 'snake', 'goat'],
      cities: ['Tunis', 'Sfax', 'Sousse', 'Kairouan', 'Bizerte'] },
    { name: 'Algeria', flag: '🇩🇿', region: 'North Africa',
      animals: ['camel', 'antelope', 'fox', 'eagle', 'monkey', 'snake'],
      cities: ['Algiers', 'Oran', 'Constantine', 'Annaba', 'Batna'] },
    { name: 'Morocco', flag: '🇲🇦', region: 'North Africa',
      animals: ['camel', 'goat', 'fox', 'eagle', 'monkey', 'snake'],
      cities: ['Casablanca', 'Rabat', 'Marrakesh', 'Fes', 'Tangier', 'Agadir'] },
    // ---- Island nations ----
    { name: 'Madagascar', flag: '🇲🇬', region: 'Indian Ocean',
      animals: ['monkey', 'chameleon', 'turtle', 'bat', 'parrot', 'fish'],
      cities: ['Antananarivo', 'Toamasina', 'Antsirabe', 'Mahajanga', 'Toliara'] },
    { name: 'Mauritius', flag: '🇲🇺', region: 'Indian Ocean',
      animals: ['dodo', 'turtle', 'dolphin', 'bat', 'fish', 'crab'],
      cities: ['Port Louis', 'Beau Bassin', 'Curepipe', 'Quatre Bornes'] },
    { name: 'Seychelles', flag: '🇸🇨', region: 'Indian Ocean',
      animals: ['turtle', 'shark', 'dolphin', 'owl', 'fish', 'crab'],
      cities: ['Victoria', 'Anse Boileau', 'Beau Vallon'] },
    { name: 'Comoros', flag: '🇰🇲', region: 'Indian Ocean',
      animals: ['bat', 'turtle', 'dolphin', 'parrot', 'fish', 'crab'],
      cities: ['Moroni', 'Mutsamudu', 'Fomboni'] },
  ];

  /*
   * Build the whole campaign. Difficulty rises twice over: gently across
   * the cities within a country, and steadily across the tour as a whole,
   * so a country's first city is always a breather after the last one's
   * finale — without ever getting easier than where you have been.
   */
  /*
   * Difficulty is POINTS REQUIRED PER MOVE, not the raw target. A late
   * stage has fewer moves, so a target that only ever climbed would
   * become arithmetically impossible — the first cut of this curve ended
   * up demanding 132,000 points in 13 moves. Points-per-move rises
   * steadily from easy (190, against the ~550 a decent player scores) to
   * demanding (620, which needs real cascades), and because it is a
   * function of the global stage number, every city is harder than the
   * one before it — inside a country and across the whole tour.
   */
  const PPM_START = 190;
  const PPM_END = 620;

  function buildCampaign(countries, colors) {
    const list = countries || COUNTRIES;
    const slots = colors || 6;
    const levels = [];
    const index = [];
    const totalStages = list.reduce(function (a, c) { return a + c.cities.length; }, 0);

    list.forEach(function (country, ci) {
      const from = levels.length;
      country.cities.forEach(function (city, cityIdx) {
        const g = levels.length;                       // global stage number
        const progress = totalStages > 1 ? g / (totalStages - 1) : 0;

        const moves = Math.max(14, 25 - Math.floor(g / 22));
        const ppm = PPM_START + (PPM_END - PPM_START) * progress;
        const target = Math.round((moves * ppm) / 10) * 10;

        const collect = [];
        if (g >= 2) {
          collect.push({ c: (ci + cityIdx) % slots, n: Math.min(30, 14 + Math.floor(g / 20)) });
        }
        if (g >= 10) {
          collect.push({ c: (ci + cityIdx + 3) % slots, n: Math.min(28, 12 + Math.floor(g / 26)) });
        }

        levels.push({
          n: g + 1,
          city,
          cityIndex: cityIdx,
          countryIndex: ci,
          country: country.name,
          flag: country.flag,
          region: country.region,
          animals: country.animals,
          blurb: city,
          moves,
          target,
          collect,
          ppm: Math.round(ppm),
        });
      });
      index.push({
        name: country.name,
        flag: country.flag,
        region: country.region,
        animals: country.animals,
        countryIndex: ci,
        firstLevel: from + 1,
        lastLevel: levels.length,
        cityCount: country.cities.length,
      });
    });

    return { levels, index };
  }

  /* The six animals in play for a given level, as full records. */
  function animalsFor(level) {
    return (level.animals || COUNTRIES[0].animals).map(function (key) {
      const a = ANIMALS[key] || ANIMALS.lion;
      return { key: key, g: a.g, en: a.en, voice: a.voice };
    });
  }

  const Atlas = { ANIMALS, COUNTRIES, buildCampaign, animalsFor };

  if (typeof module !== 'undefined' && module.exports) module.exports = Atlas;
  else global.NairobiAtlas = Atlas;
})(typeof window !== 'undefined' ? window : globalThis);
