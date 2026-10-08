"""Static demo content used by `seed_demo`: blog posts, FAQs, testimonials, localities."""

# (name, tehsil, type, lat, lng, featured, residential rate/sqm, agricultural rate/sqm)
LOCALITIES = [
    ("Fatehabad Road", "Agra Sadar", "urban", 27.1600, 78.0560, True, 42000, None),
    ("Shamshabad Road", "Agra Sadar", "highway", 27.1420, 78.0250, True, 24000, 1400),
    ("Sikandra", "Agra Sadar", "urban", 27.2190, 77.9520, True, 30000, None),
    ("Kamla Nagar", "Agra Sadar", "urban", 27.2110, 78.0240, True, 45000, None),
    ("Dayalbagh", "Agra Sadar", "urban", 27.2260, 78.0090, False, 33000, None),
    ("Shastripuram", "Agra Sadar", "urban", 27.2010, 77.9370, True, 26000, None),
    ("Tajganj", "Agra Sadar", "urban", 27.1640, 78.0460, False, 38000, None),
    ("Kalindi Vihar", "Agra Sadar", "urban", 27.2060, 78.0520, False, 22000, None),
    ("Agra-Lucknow Expressway Belt", "Etmadpur", "highway", 27.2330, 78.1450, True, 14000, 1600),
    ("Yamuna Expressway Belt", "Etmadpur", "highway", 27.2440, 78.0950, True, 16000, 1800),
    ("Gwalior Road", "Agra Sadar", "highway", 27.1290, 77.9880, False, 18000, 1200),
    ("Runkata", "Kiraoli", "highway", 27.2370, 77.8930, False, 12000, 1100),
    ("Etmadpur", "Etmadpur", "village", 27.2360, 78.2000, False, 8000, 700),
    ("Kiraoli", "Kiraoli", "village", 27.1380, 77.7830, False, 7000, 550),
    ("Fatehpur Sikri", "Fatehpur Sikri", "village", 27.0940, 77.6620, False, 9000, 650),
    ("Bichpuri", "Agra Sadar", "village", 27.1960, 77.9110, False, 11000, 900),
    ("Artoni", "Agra Sadar", "village", 27.2410, 77.9310, False, 13000, 1000),
    ("Kheragarh", "Kheragarh", "village", 26.9600, 77.8300, False, 6000, 450),
    ("Fatehabad Town", "Fatehabad", "village", 27.0260, 78.3030, False, 6500, 500),
    ("Bah", "Bah", "village", 26.8690, 78.5960, False, 5000, 400),
]

LOCALITY_TEXT = {
    "Fatehabad Road": (
        "Fatehabad Road is Agra's premium hotel and residential corridor near the Taj East Gate. Demand for residential and commercial plots stays strong because of hotels, hospitals and new gated colonies.",
        "Direct road to Taj East Gate\n4 km to Agra Cantt railway station\nConnects to Agra-Lucknow Expressway via Fatehabad",
        "Hotel belt near Taj East Gate\nShilpgram\nAmar Vilas / Oberoi area",
    ),
    "Shamshabad Road": (
        "Shamshabad Road is one of the fastest growing belts in south Agra with new colonies, schools and farmhouses. Both plots and agricultural land are in demand here.",
        "Connects Agra city to Shamshabad town\nClose to Inner Ring Road\nEasy access to Fatehabad Road",
        "Inner Ring Road crossing\nNew township projects\nSchools and colleges",
    ),
    "Sikandra": (
        "Sikandra in west Agra is known for Akbar's Tomb and the Sikandra industrial area. Residential plots near NH-19 and Awas Vikas colonies sell quickly.",
        "On NH-19 (Agra-Delhi highway)\nNear ISBT Agra\nClose to Sikandra industrial area",
        "Akbar's Tomb\nISBT Agra\nAwas Vikas Colony",
    ),
    "Kamla Nagar": (
        "Kamla Nagar is a mature, high demand residential and market area in north Agra. Small plots and old houses on main roads get excellent prices.",
        "Close to MG Road\nNear Agra Fort railway station\nWell connected to Bypass Road",
        "Kamla Nagar market\nBalkeshwar\nYamuna Kinara road",
    ),
    "Dayalbagh": (
        "Dayalbagh is a calm, green residential area with planned colonies and educational institutes. Plots here are preferred by families looking for long-term homes.",
        "Connected to Bhagwan Talkies and Sikandra\nNear Dayalbagh Educational Institute",
        "Soami Bagh\nDayalbagh Educational Institute",
    ),
    "Shastripuram": (
        "Shastripuram is a large planned residential area in west Agra developed by ADA and Awas Vikas, popular for mid-budget plots.",
        "Near Sikandra and NH-19\nClose to Inner Ring Road",
        "Shastripuram market\nVidya Nagar",
    ),
    "Tajganj": (
        "Tajganj, the historic area around the Taj Mahal, has strong demand for commercial plots, guest houses and shops, within heritage rules.",
        "Walking distance to Taj Mahal\nConnected to Fatehabad Road",
        "Taj Mahal\nTajganj market",
    ),
    "Kalindi Vihar": (
        "Kalindi Vihar across the Yamuna is an affordable residential area seeing new demand due to better bridges and the expressway link.",
        "Close to Yamuna bridge\nNear Agra-Lucknow Expressway start",
        "Kalindi Vihar market\nRamnagar",
    ),
    "Agra-Lucknow Expressway Belt": (
        "The Agra-Lucknow Expressway belt around Etmadpur is the hottest zone for farmhouse land, warehouse land and long-term agricultural investment.",
        "Direct expressway access\nNear Yamuna Expressway junction\nUpcoming logistics and industrial parks",
        "Expressway toll plaza\nEtmadpur town",
    ),
    "Yamuna Expressway Belt": (
        "Land along the Yamuna Expressway near Agra is in demand from investors, warehouse operators and farmhouse buyers from Delhi NCR.",
        "Yamuna Expressway to Greater Noida\nLink to Agra-Lucknow Expressway",
        "Kuberpur interchange\nTundla road",
    ),
    "Gwalior Road": (
        "Gwalior Road (NH-44) south of Agra city is a commercial and warehousing corridor with demand for highway-facing land.",
        "On NH-44 towards Gwalior\nNear Agra Cantt",
        "Agra Cantt\nTransport Nagar",
    ),
    "Runkata": (
        "Runkata on the Agra-Mathura highway (NH-19) has demand for industrial land, highway frontage and residential plots near the Keetham lake area.",
        "On NH-19 towards Mathura\nNear Keetham",
        "Sur Sarovar (Keetham Lake)\nRunkata market",
    ),
    "Etmadpur": (
        "Etmadpur tehsil east of the Yamuna has large agricultural land parcels with growing interest because of both expressways nearby.",
        "Agra-Firozabad road\nClose to Agra-Lucknow Expressway",
        "Etmadpur tehsil office\nTundla junction",
    ),
    "Kiraoli": (
        "Kiraoli tehsil on the Agra-Jaipur road is mostly agricultural with fertile land and steady demand from farmers and investors.",
        "Agra-Jaipur highway (NH-21)\nRoad to Fatehpur Sikri",
        "Kiraoli tehsil office\nAchhnera",
    ),
    "Fatehpur Sikri": (
        "Fatehpur Sikri, the UNESCO heritage town, has agricultural land and small plots with tourism-driven commercial interest on the main road.",
        "Agra-Jaipur highway\nFatehpur Sikri railway station",
        "Buland Darwaza\nFatehpur Sikri monuments",
    ),
    "Bichpuri": (
        "Bichpuri is an emerging belt west of Agra with educational institutes and new colonies on the Bichpuri road.",
        "Connected to NH-19 and Inner Ring Road\nNear Agra College campus",
        "RBS College Bichpuri campus\nBichpuri road",
    ),
    "Artoni": (
        "Artoni near Sikandra is seeing new residential colonies and farmhouse plots close to the Agra-Delhi highway.",
        "Near NH-19\nClose to Sikandra",
        "Artoni village\nKeetham road",
    ),
    "Kheragarh": (
        "Kheragarh tehsil in south-west Agra has large agricultural holdings with lower prices per bigha and good long-term potential.",
        "Agra-Kheragarh road\nNear Rajasthan border",
        "Kheragarh tehsil office",
    ),
    "Fatehabad Town": (
        "Fatehabad town and tehsil in east Agra is an agricultural area that benefits from the Agra-Lucknow Expressway access point.",
        "Fatehabad road from Agra city\nExpressway access near Fatehabad",
        "Fatehabad tehsil office",
    ),
    "Bah": (
        "Bah tehsil along the Chambal side is a rural agricultural area with large parcels and very affordable land rates.",
        "Agra-Bah road\nNear Chambal sanctuary",
        "Bah tehsil office\nBateshwar temples",
    ),
}

TESTIMONIALS = [
    ("Ramesh Chand Sharma", "Etmadpur", "4 bigha agricultural land",
     "Brokers kept bringing buyers for a year and nobody paid. BhoomiDirect visited my khet within 3 days, gave a written offer and the registry was done in 3 weeks with full RTGS payment."),
    ("Sunita Agarwal", "Kamla Nagar", "180 gaj plot with old house",
     "We are three sisters and the property was joint. Their legal team explained everything and handled the paperwork. Very respectful and transparent."),
    ("Mohd. Iqbal", "Sikandra", "250 gaj residential plot",
     "The offer was fair and close to market. No commission, no drama. I tracked every step online with my reference ID."),
    ("Harpal Singh", "Fatehabad Road", "Commercial plot",
     "I needed money urgently for my son's business. They closed the deal in 18 days. Recommended for anyone in Agra."),
    ("Kamlesh Devi", "Kiraoli", "2.5 bigha land",
     "My son works in Delhi, so I was worried about the process. Their agent came to the village, explained in Hindi and helped with the khatauni."),
    ("Vivek Gupta", "Shamshabad Road", "Farmhouse land",
     "Clear valuation with circle rate comparison. I accepted the counter offer from my dashboard and registry happened the next week."),
]

FAQS = [
    ("selling", "Do you charge any commission or fee?", "No. We buy your property directly, so there is no brokerage or evaluation fee. Registry costs like stamp duty are paid by us as the buyer.", True),
    ("selling", "What types of property do you buy in Agra?", "Residential plots, commercial plots, agricultural land, farmhouse land, industrial land and plots with old construction across all 7 tehsils of Agra district.", True),
    ("selling", "How fast can I get an offer?", "Usually within 7 days of the site visit. Urgent cases can be faster once documents are clear.", True),
    ("selling", "Is there any obligation after I submit?", "No. Submitting is free and you can decline our offer at any time before signing the agreement.", False),
    ("legal", "Which documents do I need?", "Registry or sale deed, latest Khatauni (for agricultural land), mutation order, ID proof of all owners and any site map. If something is missing, our legal team will guide you.", True),
    ("legal", "Can I sell joint family property?", "Yes, if all co-owners named in the records agree and sign at registry. We help coordinate signatures and power of attorney if needed.", False),
    ("legal", "What if there is a loan on the land?", "We can still buy. The loan is usually closed from the sale amount at registry with a NOC from the bank.", False),
    ("payment", "How will I receive the payment?", "Full payment by RTGS / NEFT or demand draft at the time of registry at the sub-registrar office.", True),
    ("payment", "How do you decide the price?", "We look at sample circle rate, recent deals, road access, size, legal clarity and resale demand. You can see the reasoning when we share the offer.", False),
    ("payment", "Can I negotiate the offer?", "Yes. You can accept, reject or send a counter offer from your owner dashboard.", False),
    ("buying", "Are the properties on your website verified?", "Yes. Every listed property is already purchased by us with clear title, so buyers get a clean registry directly from the company.", False),
    ("buying", "Can brokers sell your inventory?", "Yes. Registered channel partners can refer buyers and earn commission. See the Channel Partners page.", False),
]

BLOG_CATEGORIES = ["Legal Guides", "Selling Tips", "Market Insights"]

BLOG_POSTS = [
    {
        "title": "How to Sell Agricultural Land in Agra: Documents Checklist",
        "category": "Legal Guides",
        "excerpt": "Planning to sell khet or agricultural land in Agra district? Here is the complete list of documents buyers and the sub-registrar will ask for, and how to get each one.",
        "content": """
<p>Selling agricultural land in Agra is simple when your papers are ready. Most delays happen because one document is missing or does not match the land records. Use this checklist before you talk to any buyer.</p>
<h2>1. Khatauni (record of rights)</h2>
<p>The Khatauni shows who the khatedar (owner) of each khasra number is. Download the latest copy from the UP Bhulekh portal or get a certified copy from the tehsil. Check that:</p>
<ul><li>All owners' names are spelled correctly</li><li>The khasra / gata number and area match what you are selling</li><li>There is no entry of loan, lease or government acquisition</li></ul>
<h2>2. Registry / sale deed</h2>
<p>If you bought the land, keep your original registry. If it came through inheritance, keep the earlier registry of your father or grandfather and the mutation order in your name.</p>
<h2>3. Mutation (Dakhil Kharij) order</h2>
<p>Mutation updates the revenue records in your name. A buyer will not pay full price if mutation is pending. Read our guide on the <a href="/blog/mutation-dakhil-kharij-process-in-up/">Dakhil Kharij process in UP</a>.</p>
<h2>4. Identity and PAN of all owners</h2>
<p>Aadhaar and PAN are required for every seller. If the sale value is above ₹ 50 lakh, TDS rules apply and PAN is mandatory.</p>
<h2>5. Map / naksha and boundaries</h2>
<p>A simple hand map with neighbouring khasra numbers helps the buyer's field team verify the land on the ground.</p>
<h2>6. NOC if applicable</h2>
<ul><li>Bank NOC if there was a kisan credit card or land loan</li><li>Consent of all co-owners in joint land</li></ul>
<h2>Quick checklist</h2>
<table><tr><th>Document</th><th>Where to get it</th></tr>
<tr><td>Khatauni</td><td>UP Bhulekh / tehsil</td></tr>
<tr><td>Registry / sale deed</td><td>Your records / sub-registrar office</td></tr>
<tr><td>Mutation order</td><td>Tehsildar court</td></tr>
<tr><td>Aadhaar, PAN</td><td>All owners</td></tr></table>
<blockquote>Missing a document? You can still submit your land to us. Our legal desk will tell you exactly what is needed.</blockquote>
""",
    },
    {
        "title": "Khatauni vs Registry: What Buyers Check",
        "category": "Legal Guides",
        "excerpt": "Registry proves a sale happened. Khatauni proves who the revenue records show as owner. Serious buyers check both. Here's the difference.",
        "content": """
<p>Many land owners in Agra believe that having the registry is enough to sell. Buyers, banks and companies like ours always check two things: the <strong>registry</strong> and the <strong>Khatauni</strong>.</p>
<h2>What is a registry?</h2>
<p>A registry (sale deed) is the document registered at the sub-registrar office when a property is sold. It proves that a transfer happened between a seller and a buyer on a certain date for a certain price.</p>
<h2>What is a Khatauni?</h2>
<p>The Khatauni is the revenue record maintained by the tehsil. It lists the khatedars (owners) for each khasra number along with the area and type of land.</p>
<h2>Why both matter</h2>
<ul>
<li>If the registry is in your name but the Khatauni still shows the old owner, mutation is pending.</li>
<li>If the Khatauni shows more co-owners than the registry, all of them must sign.</li>
<li>If the area in Khatauni is less than claimed, the price will be calculated on the recorded area.</li>
</ul>
<h2>What we check during legal verification</h2>
<ol><li>30-year title chain of registries</li><li>Latest Khatauni and khasra map</li><li>Mutation order</li><li>Encumbrance (loans, court cases)</li><li>Owner identity</li></ol>
<p>When both documents match, the deal moves fast and the price is better.</p>
""",
    },
    {
        "title": "Circle Rate in Agra Explained",
        "category": "Market Insights",
        "excerpt": "What is the circle rate, how it affects stamp duty, and why the market price of your plot can be higher or lower than the circle rate.",
        "content": """
<p>The circle rate is the minimum value per square metre (or per hectare for agricultural land) fixed by the District Magistrate for registering a property. In Agra, the list is published locality-wise and revised from time to time.</p>
<h2>Why circle rate matters</h2>
<ul><li><strong>Stamp duty</strong> is calculated on the higher of the circle rate value or the actual sale price.</li><li>It gives a <strong>floor value</strong> for negotiations.</li><li>Banks use it as one input for loan valuation.</li></ul>
<h2>Circle rate vs market price</h2>
<p>In prime areas like Kamla Nagar or Fatehabad Road, market prices are often well above circle rate. In remote villages they can be close to or even below the circle rate.</p>
<h2>How to calculate circle rate value</h2>
<p>Circle rate value = area in sq m × rate per sq m. For example, a 200 gaj (≈ 167 sq m) plot at ₹ 30,000 per sq m has a circle value of about ₹ 50 lakh.</p>
<blockquote>Our <a href="/price-estimator/">price estimator</a> uses sample circle rates and a market multiplier to show an indicative range. The rates on this demo website are samples, not official figures.</blockquote>
<h2>Where to find official rates</h2>
<p>Check the latest circle rate list at the Agra collectorate or the official IGRS UP portal before any transaction.</p>
""",
    },
    {
        "title": "Why Sell Land Directly Instead of Through a Broker",
        "category": "Selling Tips",
        "excerpt": "Brokers bring buyers. A direct buyer brings money. Compare commission, time to close and certainty before you decide.",
        "content": """
<p>Most land in Agra changes hands through one or more brokers. That works for some owners, but it has hidden costs.</p>
<h2>The broker route</h2>
<ul><li>1% to 2% commission, sometimes on both sides</li><li>Many site visits with buyers who are "just checking"</li><li>Token money that gets cancelled at the last minute</li><li>Price pressure as the listing gets old</li></ul>
<h2>The direct buyer route</h2>
<ul><li>No commission</li><li>One evaluation, one site visit, one written offer</li><li>Legal check done by the buyer's team for free</li><li>Full payment at registry</li></ul>
<h2>Comparison</h2>
<table><tr><th></th><th>Broker</th><th>Direct to company</th></tr>
<tr><td>Commission</td><td>1-2%</td><td>0%</td></tr>
<tr><td>Typical time</td><td>3-12 months</td><td>2-4 weeks</td></tr>
<tr><td>Certainty</td><td>Low until registry</td><td>Written offer</td></tr></table>
<h2>When a broker may still be right</h2>
<p>If you have time and want to test the market for a unique property, a broker can help. If you want speed, certainty and less hassle, a direct sale is usually better.</p>
""",
    },
    {
        "title": "Mutation (Dakhil Kharij) Process in UP",
        "category": "Legal Guides",
        "excerpt": "Step-by-step guide to getting mutation (dakhil kharij) done in Uttar Pradesh after purchase or inheritance, with timelines and common problems.",
        "content": """
<p>Mutation, called <em>dakhil kharij</em> in Uttar Pradesh, updates the revenue records (Khatauni) to show the new owner after a sale, gift or inheritance.</p>
<h2>When is mutation needed?</h2>
<ul><li>After you buy land through registry</li><li>After the death of the recorded owner (succession / varasat)</li><li>After a gift deed or family partition</li></ul>
<h2>Step-by-step process</h2>
<ol>
<li>Apply online on the UP Bhulekh / revenue court portal or at the tehsil with the registry copy.</li>
<li>The Lekhpal verifies and submits a report.</li>
<li>A public notice is issued so objections can be filed (usually 30-45 days).</li>
<li>If no objection, the Tehsildar passes the mutation order.</li>
<li>The Khatauni is updated with your name.</li>
</ol>
<h2>Documents</h2>
<ul><li>Certified copy of registry</li><li>Aadhaar of applicant</li><li>Death certificate and family register (for varasat)</li></ul>
<h2>Common problems</h2>
<ul><li>Objections from relatives</li><li>Area mismatch between registry and records</li><li>Old registries without khasra numbers</li></ul>
<blockquote>Mutation pending? You can still submit your land. We guide owners through dakhil kharij as part of our purchase process.</blockquote>
""",
    },
    {
        "title": "Best Growing Areas for Land in Agra",
        "category": "Market Insights",
        "excerpt": "From the Agra-Lucknow Expressway belt to Shamshabad Road, these are the areas where land demand and prices are rising the fastest.",
        "content": """
<p>Agra is growing beyond the old city. Expressways, the Inner Ring Road and new townships are creating demand in new belts. Here are the areas we see the most buyer interest in.</p>
<h2>1. Agra-Lucknow Expressway belt</h2>
<p>Farmhouse land, warehouses and logistics parks are driving demand around Etmadpur and the expressway start point.</p>
<h2>2. Yamuna Expressway belt</h2>
<p>Investors from Delhi NCR are buying land near the Yamuna Expressway end point for long-term appreciation.</p>
<h2>3. Shamshabad Road</h2>
<p>New colonies, schools and the Inner Ring Road link make this one of the best mid-budget plot markets.</p>
<h2>4. Fatehabad Road</h2>
<p>The premium hotel corridor continues to command top prices for residential and commercial plots.</p>
<h2>5. Sikandra and Runkata</h2>
<p>Industrial and highway demand on NH-19 keeps both residential and commercial land active.</p>
<h2>What this means for owners</h2>
<p>If you own land in these belts, get a fresh valuation. Prices from even two years ago may be outdated. <a href="/sell-land-in-agra/">See all areas we buy in</a>.</p>
""",
    },
]

OWNER_NAMES = [
    "Rakesh Kumar", "Suresh Chand Yadav", "Anita Sharma", "Mahesh Prasad", "Geeta Devi", "Rajendra Singh Chauhan",
    "Pooja Agarwal", "Vinod Kumar Jain", "Shyam Sundar Goyal", "Ram Prakash Baghel", "Neelam Gupta", "Ajay Pratap Singh",
    "Mohd. Salim", "Kusum Lata", "Devendra Kushwah", "Satish Chandra", "Meena Kumari", "Arvind Saxena",
    "Pradeep Tomar", "Laxmi Narayan", "Bhupendra Sikarwar", "Rekha Rani", "Om Prakash Verma", "Sanjay Mittal",
    "Naresh Pal", "Usha Rathore", "Hemant Bansal", "Ganga Ram", "Kailash Chand", "Shabnam Begum",
    "Dinesh Upadhyay", "Prem Singh", "Asha Khandelwal", "Yogesh Rawat", "Jagdish Prasad", "Savitri Devi",
    "Manoj Dixit", "Ravi Shankar", "Kiran Bala", "Tejveer Singh",
]

BUYER_NAMES = [
    "Amit Goel", "Priya Malhotra", "Rohit Bansal", "Faisal Khan", "Neha Chaturvedi",
    "Sandeep Arora", "Ankit Jindal", "Ritu Singhal", "Varun Kapoor", "Deepika Rawat",
]

REASONS = [
    "Need funds for daughter's wedding", "Shifting to Delhi with family", "Family partition, all owners agree",
    "Want to invest in business", "Land is far from current residence", "Medical expenses",
    "Children settled abroad", "Buying a flat in the city", "Clearing old loans", "No one to look after the land",
]

CROPS = ["Wheat", "Mustard", "Potato", "Bajra", "Paddy", "Vacant"]
