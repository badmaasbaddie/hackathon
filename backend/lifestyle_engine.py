"""
SwasthyaSetu AI — Early Precaution, Diet & Work Lifestyle Engine
Provides culturally grounded, evidence-based preventive health guidance for:
1. Minor acute symptoms occurring in 1-3 days (Headache, Fever, Loose motion, Acidity, Cough/Cold)
   - What to Do (Immediate Home Care)
   - What NOT to Do (Harmful Practices to Avoid)
   - What to Eat & Drink (Safe Nourishing Diet)
   - Foods to Avoid (Irritants & Heavy Foods)
   - Type of Work to Accomplish & Physical Activity Limits
   - Red Flag Warnings (When to Rush to Clinic)

2. Post-Checkup & Disease-Specific Care Plans (Hypertension, Diabetes, Cardiac/Angina, Anemia, Asthma)
   - Diet to Eat & Diet to Avoid
   - Type of Daily Work Allowed vs Heavy Physical Labor Restrictions
   - Medication Adherence & Timing with Meals
"""

from typing import Dict, Any, List

def generate_early_precautions_and_diet(text: str, language: str = "hi", duration_days: int = 2) -> Dict[str, Any]:
    text_lower = text.lower()

    # 1. LOOSE MOTION / DIARRHEA / DAST
    if any(k in text_lower for k in ["loose motion", "loose motions", "dast", "pet kharab", "diarrhea", "diarrhoea", "watery stool", "latrine", "bar bar toilet", "stomach upset", "loose stool"]):
        if language == "hi":
            return {
                "condition_detected": "दस्त / पेट खराब (Loose Motion / Diarrhea)",
                "what_to_do": [
                    "प्रत्येक दस्त के बाद तुरंत 1 गिलास ORS (जीवन रक्षक घोल) या नमक-चीनी का पानी पिएं।",
                    "स्वच्छ उबला हुआ और ठंडा किया हुआ पानी ही पिएं ताकि शरीर में पानी की कमी न हो।",
                    "शौच के बाद और भोजन से पहले साबुन से अच्छी तरह हाथ धोएं।",
                    "घर पर पूर्ण विश्राम करें और शरीर को ठंडा रखें।"
                ],
                "what_not_to_do": [
                    "बिना डॉक्टर की सलाह के मेडिकल स्टोर से उल्टी-दस्त रोकने वाली तेज गोलियां (जैसे लोपेरामाइड) न लें।",
                    "तरल पदार्थ पीना बिल्कुल बंद न करें — डिहाइड्रेशन ही सबसे बड़ा खतरा है।",
                    "खुले में रखा, बासी या बाजार का स्ट्रीट फूड कतई न खाएं।",
                    "कड़क चाय, कॉफी या अधिक मीठे पैकेट वाले शरबत न पिएं।"
                ],
                "diet_to_eat": [
                    "ताजा मट्ठा / पतली छाछ भुने जीरे और हल्के नमक के साथ (पेट के लिए अमृत)।",
                    "पतली मूंग दाल की खिचड़ी, सादा उबला चावल और दही।",
                    "पका हुआ केला (पोटैशियम की कमी पूरी करता है) और उबला आलू।",
                    "नारियल पानी, नींबू-शिकंजी और हल्का दलिया।"
                ],
                "diet_to_avoid": [
                    "पूरी, पराठा, समोसा, पकोड़े जैसे तैलीय और तले-भुने पकवान।",
                    "लाल मिर्च, गरम मसाला और अधिक तेल वाली भारी सब्जियां।",
                    "कच्चा दूध, पनीर या भारी मावे की मिठाइयां।",
                    "बाजार के कोल्ड ड्रिंक्स और कच्ची बिना छिलके वाली सब्जियां।"
                ],
                "activity_and_work_guidance": [
                    "सुरक्षित कार्य: घर पर हल्के काम या बैठने वाले कार्य ही करें।",
                    "वर्जित शारीरिक श्रम: धूप में खेती का काम, भारी वजन उठाना (बोरी/बाल्टी) या लंबी यात्रा तुरंत टालें।",
                    "अचानक खड़े होने पर चक्कर आ सकते हैं, इसलिए धीरे-धीरे उठें।"
                ],
                "red_flag_warnings": [
                    "मल में खून या आंव (म्यूकस) आना।",
                    "लगातार उल्टी होना जिससे पानी भी पेट में न रुके।",
                    "6 घंटे से पेशाब न होना, आंखें धंस जाना या अत्यधिक कमजोरी।",
                    "यदि 2 दिन में सुधार न हो तो तुरंत नजदीकी CHC/PHC अस्पताल पहुंचे।"
                ]
            }
        else:
            return {
                "condition_detected": "Loose Motion / Acute Diarrhea (Mild)",
                "what_to_do": [
                    "Drink 1 glass of Oral Rehydration Solution (ORS) after every loose stool.",
                    "Drink only boiled, cooled, clean water to prevent dehydration.",
                    "Wash hands thoroughly with soap before eating and after toilet use.",
                    "Take complete bed rest in a well-ventilated, shaded room."
                ],
                "what_not_to_do": [
                    "Do NOT take unprescribed anti-motility pills (like loperamide) without doctor advice.",
                    "Never restrict fluid intake — fluid depletion is the primary risk.",
                    "Do NOT consume roadside or uncovered food.",
                    "Avoid commercial sodas, strong black tea, and energy drinks."
                ],
                "diet_to_eat": [
                    "Fresh buttermilk / curd with roasted cumin and a pinch of salt (natural probiotic).",
                    "Soft moong dal khichdi, boiled white rice with light curd.",
                    "Ripe bananas (restores essential potassium) and boiled potatoes.",
                    "Tender coconut water, light apple compote, and thin vegetable broth."
                ],
                "diet_to_avoid": [
                    "Deep-fried items, oily curries, samosas, and pakoras.",
                    "Spicy red chilli and heavy garam masala preparations.",
                    "Whole buffalo milk, heavy cheese, and cream-based sweets.",
                    "Raw salads, carbonated beverages, and unpasteurized fruit juices."
                ],
                "activity_and_work_guidance": [
                    "Permitted Work: Light sedentary desk work, reading, or quiet indoor chores.",
                    "Physical Exertion to AVOID: Outdoor field labor, heavy agricultural lifting, or direct hot sun exposure.",
                    "Change posture slowly to prevent orthostatic dizziness."
                ],
                "red_flag_warnings": [
                    "Presence of blood or mucus in stools (dysentery).",
                    "Intractable vomiting preventing oral fluid retention.",
                    "No urine output for over 6 hours, sunken eyes, or extreme dry mouth.",
                    "If symptoms persist beyond 48 hours, seek immediate evaluation at CHC/hospital."
                ]
            }

    # 2. FEVER / BUKHAR
    if any(k in text_lower for k in ["fever", "bukhar", "tap", "halka bukhar", "hararat", "chills", "badan garm", "temperature", "pyrexia"]):
        if language == "hi":
            return {
                "condition_detected": "बुखार / हरारत (Fever - 1 to 3 days)",
                "what_to_do": [
                    "सादे कमरे के तापमान वाले पानी से माथे, गर्दन और बगलों पर गीली सूती पट्टी रखें (ठंडी सिकाई)।",
                    "हल्के, ढीले सूती कपड़े पहनें ताकि शरीर की गर्मी बाहर निकल सके।",
                    "थर्मामीटर से हर 4 से 6 घंटे पर तापमान नोट करें।",
                    "पर्याप्त मात्रा में पानी, गुनगुना सूप और तरल पदार्थ पीकर शरीर को हाइड्रेटेड रखें।"
                ],
                "what_not_to_do": [
                    "बर्फ जैसे बहुत ठंडे पानी की पट्टी कभी न रखें (इससे कंपकंपी छूट सकती है)।",
                    "बुखार में मरीज को मोटे कंबल या रजाई में अत्यधिक न लपेटें।",
                    "बिना डॉक्टर के पर्चे के मेडिकल स्टोर से एंटीबायोटिक्स शुरू न करें।",
                    "भूखे पेट न रहें — बीमारी से लड़ने के लिए ऊर्जा जरूरी है।"
                ],
                "diet_to_eat": [
                    "मूंग दाल की पतली खिचड़ी, दलिया या सूजी की खीर (कम चीनी)।",
                    "हल्का गुनगुना टमाटर या मिश्रित सब्जियों का सूप।",
                    "गुनगुना पानी, नारियल पानी और मौसमी फल जैसे सेब, चीकू, अनार।",
                    "रात को हल्का हल्दी वाला गुनगुना दूध (यदि कफ न हो)।"
                ],
                "diet_to_avoid": [
                    "फ्रिज का ठंडा पानी, आइसक्रीम या ठंडे पेय पदार्थ।",
                    "तली-भुनी पूरियां, पराठे, चाट और गरिष्ठ मांसाहारी भोजन।",
                    "खट्टी और बासी चीजें।"
                ],
                "activity_and_work_guidance": [
                    "सुरक्षित कार्य: 24 से 48 घंटे पूर्ण आराम करें; केवल जरूरी घरेलू कार्य ही करें।",
                    "वर्जित शारीरिक श्रम: खेत में हल चलाना, वजन उठाना, तेज धूप में दौड़ना या बाइक चलाना बंद रखें।",
                    "बुखार उतरने के 24 घंटे बाद ही सामान्य काम पर लौटें।"
                ],
                "red_flag_warnings": [
                    "बुखार 103°F से अधिक बढ़ जाना या दवा के बाद भी बिल्कुल न उतरना।",
                    "गर्दन में अत्यधिक जकड़न, तेज सिरदर्द या चमकी (दौरे) आना।",
                    "सांस लेने में कठिनाई या शरीर पर लाल चकत्ते (रैश) उभरना।",
                    "3 दिन से अधिक बुखार बने रहने पर तुरंत मलेरिया/डेंगू/टाइफाइड जांच कराएं।"
                ]
            }
        else:
            return {
                "condition_detected": "Acute Fever / Pyrexia (1 to 3 days)",
                "what_to_do": [
                    "Apply room-temperature wet cloth compresses to forehead and neck (tepid sponging).",
                    "Wear lightweight, breathable loose cotton clothing to dissipate heat.",
                    "Record body temperature with a digital thermometer every 4-6 hours.",
                    "Maintain continuous hydration with lukewarm water and broths."
                ],
                "what_not_to_do": [
                    "Do NOT use freezing ice water (causes intense shivering and rebound heat).",
                    "Avoid smothering under thick, heavy blankets.",
                    "Do NOT take self-prescribed antibiotics without clinician guidance.",
                    "Never fast or skip meals during fever."
                ],
                "diet_to_eat": [
                    "Moong dal khichdi, thin vegetable porridge (daliya), and clear soups.",
                    "Warm boiled cooled water, tender coconut water, and diluted citrus juices.",
                    "Easily digestible fruits: steamed apples, ripe bananas, papayas.",
                    "Lukewarm water with a pinch of turmeric and ginger."
                ],
                "diet_to_avoid": [
                    "Refrigerated chilled drinks, ice creams, and ice cubes.",
                    "Oily fried snacks, spicy heavy meats, and roadside food.",
                    "Stale, fermented, or heavy dairy preparations."
                ],
                "activity_and_work_guidance": [
                    "Permitted Work: Complete bed rest for the first 24-48 hours.",
                    "Physical Exertion to AVOID: Strenuous farm labor, heavy weight lifting, long motorcycle commutes, or outdoor sun exposure.",
                    "Resume routine work only after remaining afebrile for 24 continuous hours."
                ],
                "red_flag_warnings": [
                    "Temperature exceeding 103°F (39.4°C) or unresponsive to paracetamol.",
                    "Stiff neck, confusion, delirium, or febrile convulsions.",
                    "Shortness of breath, persistent vomiting, or petechial skin rashes.",
                    "Fever lasting >3 days requires lab screening for Malaria/Dengue/Typhoid at CHC."
                ]
            }

    # 3. HEADACHE / SIR DARD
    if any(k in text_lower for k in ["headache", "sir dard", "sar dard", "sir me dard", "sar me dard", "heavy head", "matha dard", "adhasisi", "migraine"]):
        if language == "hi":
            return {
                "condition_detected": "सिरदर्द / सिर में भारीपन (Headache - Recent)",
                "what_to_do": [
                    "शांत, हल्के अंधेरे और हवादार कमरे में 30-45 मिनट लेटकर आंखें बंद करें।",
                    "तुरंत 2-3 गिलास साफ पानी पिएं (अधिकांश सिरदर्द पानी की कमी से होते हैं)।",
                    "माथे और गर्दन के पीछे ठंडे या गुनगुने गीले कपड़े से हल्की सिकाई करें।",
                    "गहरी सांस लेने का व्यायाम (प्राणायाम) करें और 7-8 घंटे की पूरी नींद लें।"
                ],
                "what_not_to_do": [
                    "मोबाइल फोन, टीवी या कंप्यूटर स्क्रीन की तेज रोशनी में न बैठें।",
                    "तेज धूप में नंगे सिर बाहर न निकलें।",
                    "बार-बार बिना डॉक्टर की सलाह के पेनकिलर गोलियों की आदत न डालें।",
                    "भूखे पेट न रहें (एसिडिटी और खाली पेट रहने से सिरदर्द बढ़ता है)।"
                ],
                "diet_to_eat": [
                    "हल्का गुनगुना नींबू पानी या अदरक-तुलसी की हल्की चाय।",
                    "नारियल पानी और ताजे मौसमी फल (जैसे तरबूज, सेब)।",
                    "हल्का सुपाच्य भोजन — दाल, रोटी और हरी लौकी की सब्जी।",
                    "भीगे हुए बादाम या अखरोट (यदि उपलब्ध हों)।"
                ],
                "diet_to_avoid": [
                    "बहुत तेज, कड़क चाय या कॉफी का अत्यधिक सेवन।",
                    "अत्यधिक नमकीन, तीखे चिप्स या चाइनीज/अजीनोमोटो युक्त भोजन।",
                    "बासी खाना, तली-भुनी चीजें और शराब/तंबाकू/बीड़ी।"
                ],
                "activity_and_work_guidance": [
                    "सुरक्षित कार्य: धीमी गति से चलने वाले शांत घरेलू काम या विश्राम।",
                    "वर्जित शारीरिक श्रम: भारी वजन उठाना, तेज धूप में मजदूरी, तेज आवाज वाले लाउडस्पीकर/मशीनों के पास काम करना या लंबी ड्राइविंग टालें।"
                ],
                "red_flag_warnings": [
                    "अचानक बिजली की तरह तेज, असहनीय सिरदर्द होना ('Thunderclap headache')।",
                    "सिरदर्द के साथ उल्टी, गर्दन मुड़ने में तेज दर्द या धुंधला दिखाई देना।",
                    "शरीर के एक हिस्से में कमजोरी या बोलने में लड़खड़ाहट (तुरंत 112 या अस्पताल जाएं)।"
                ]
            }
        else:
            return {
                "condition_detected": "Headache / Cephalea (Recent)",
                "what_to_do": [
                    "Rest in a quiet, dark, well-ventilated room with eyes closed for 30-45 minutes.",
                    "Hydrate immediately with 2-3 glasses of clean water (dehydration is a primary trigger).",
                    "Apply a cool or warm damp washcloth across the forehead and temples.",
                    "Ensure adequate 7-8 hours of uninterrupted restful sleep."
                ],
                "what_not_to_do": [
                    "Avoid staring at mobile, television, or laptop screens.",
                    "Do NOT skip meals — reactive hypoglycemia triggers vascular headaches.",
                    "Avoid repeated unsupervised use of over-the-counter NSAIDs/painkillers.",
                    "Avoid direct hot sun exposure without head covering."
                ],
                "diet_to_eat": [
                    "Warm ginger-tulsi infusion or warm lemon water.",
                    "Tender coconut water, fresh watermelon, and ripe bananas (rich in magnesium).",
                    "Light home-cooked meals: steamed rice, yellow moong dal, and bottle gourd.",
                    "Soaked almonds and walnuts."
                ],
                "diet_to_avoid": [
                    "Excessive caffeine (more than 2 cups of strong tea/coffee).",
                    "Heavily salted snacks, pickles, processed chips, and MSG-laden foods.",
                    "Alcohol, tobacco, and fermented aged foods."
                ],
                "activity_and_work_guidance": [
                    "Permitted Work: Light desk duties, reading, and calm indoor routines.",
                    "Physical Exertion to AVOID: Heavy lifting, operating loud agricultural machinery, driving long highway distances, or strenuous outdoor manual labor."
                ],
                "red_flag_warnings": [
                    "Sudden catastrophic 'thunderclap' headache reaching peak intensity in seconds.",
                    "Headache accompanied by stiff neck, high fever, or vomiting.",
                    "Visual disturbances, limb weakness, or slurred speech (requires immediate emergency evaluation)."
                ]
            }

    # 4. ACIDITY / GAS / INDIGESTION
    if any(k in text_lower for k in ["acidity", "gas", "pet me jalan", "badhazmi", "indigestion", "khatee dakar", "bloating", "heavy stomach", "pet phoolna", "heartburn"]):
        if language == "hi":
            return {
                "condition_detected": "एसिडिटी / गैस / बदहजमी (Acidity & Indigestion)",
                "what_to_do": [
                    "ठंडा दूध (बिना चीनी) या ताजा नारियल पानी पिएं — यह पेट के एसिड को तुरंत शांत करता है।",
                    "भोजन के बाद 1 चम्मच सौंफ और मिश्री चबाएं।",
                    "खाने के तुरंत बाद न लेटें; 15-20 मिनट धीमी गति से टहलें।",
                    "सोते समय सिरहाने को थोड़ा ऊंचा रखें।"
                ],
                "what_not_to_do": [
                    "बहुत देर तक खाली पेट कतई न रहें; हर 3-4 घंटे में हल्का सुपाच्य भोजन लें।",
                    "खाना खाते ही बिस्तर पर सोने न जाएं।",
                    "तंबाकू, गुटखा, बीड़ी और सिगरेट से पूरी तरह परहेज करें (ये पेट के छालों का मुख्य कारण हैं)।",
                    "बार-बार सोडा या कोल्ड ड्रिंक न पिएं (ये गैस को बढ़ाते हैं)।"
                ],
                "diet_to_eat": [
                    "ठंडी ताजी छाछ (हल्का भुना जीरा और काला नमक डालकर)।",
                    "पका पपीता, केला, लौकी/तोरई की सादी सब्जी और पतली रोटी।",
                    "सादा ओट्स, दलिया और उबला हुआ पानी।"
                ],
                "diet_to_avoid": [
                    "लाल मिर्च, तेज गरम मसाला, तली-भुनी पूरियां, समोसे और पकौड़े।",
                    "खट्टा दही, सिरका, इमली, अचार और कच्चा प्याज/लहसुन अधिक मात्रा में।",
                    "खट्टी डकार में चाय-कॉफी पूरी तरह बंद रखें।"
                ],
                "activity_and_work_guidance": [
                    "सुरक्षित कार्य: सामान्य दैनिक काम करें; खाने के बाद 15 मिनट वज्रासन या धीमा टहलना लाभकारी है।",
                    "वर्जित शारीरिक श्रम: भोजन के तुरंत बाद आगे झुकने वाले भारी काम या पेट दबाने वाले व्यायाम न करें।"
                ],
                "red_flag_warnings": [
                    "सीने की जलन के साथ बाएं हाथ या जबड़े में दर्द और पसीना आना (यह हार्ट अटैक हो सकता है — तुरंत 112 मिलाएं)।",
                    "काले रंग का मल आना या खून की उल्टी होना।",
                    "खाना निगलने में लगातार दर्द या रुकावट होना।"
                ]
            }
        else:
            return {
                "condition_detected": "Acidity / GERD & Dyspepsia",
                "what_to_do": [
                    "Sip cold skimmed milk or tender coconut water to neutralize gastric acid.",
                    "Chew half a teaspoon of fennel seeds (saunf) after meals.",
                    "Remain upright for at least 2 hours after meals; take a gentle 15-minute walk.",
                    "Elevate head of bed by 6 inches if nocturnal acid reflux occurs."
                ],
                "what_not_to_do": [
                    "Do NOT skip meals or practice prolonged fasting.",
                    "Do NOT recline or sleep immediately after eating.",
                    "Strictly avoid tobacco, beedis, and alcohol (relaxes lower esophageal sphincter).",
                    "Avoid carbonated fizzy drinks."
                ],
                "diet_to_eat": [
                    "Fresh buttermilk with roasted cumin, cold milk.",
                    "Ripe papaya, bananas, bottle gourd, and plain whole wheat chapatis.",
                    "Oatmeal, puffed rice (murmura), and warm water."
                ],
                "diet_to_avoid": [
                    "Deep-fried snacks, samosas, spicy chutneys, and red chilli gravies.",
                    "Excessive garlic, raw onions, vinegar, and hot pickles.",
                    "Strong black coffee and citrus sodas."
                ],
                "activity_and_work_guidance": [
                    "Permitted Work: Normal office or household chores with upright posture.",
                    "Physical Exertion to AVOID: Bending forward at waist or heavy abdominal lifting immediately after meals."
                ],
                "red_flag_warnings": [
                    "Heartburn accompanied by chest pressure radiating to left arm/jaw or sweating (requires immediate emergency ECG).",
                    "Black tarry stools (melena) or vomiting blood.",
                    "Persistent dysphagia (difficulty swallowing food)."
                ]
            }

    # 5. COUGH / COLD / SORE THROAT
    if any(k in text_lower for k in ["cough", "cold", "khansi", "jukam", "zukam", "nazla", "gale me kharash", "sore throat", "runny nose", "cheenk"]):
        if language == "hi":
            return {
                "condition_detected": "जुकाम, खांसी व गले में खराश (Common Cold & Cough)",
                "what_to_do": [
                    "दिन में 2 से 3 बार हल्के गुनगुने पानी में थोड़ा नमक डालकर गरारे (Gargle) करें।",
                    "गर्म पानी की भाप (Steam inhalation) 5-10 मिनट लें ताकि बंद नाक और कफ खुले।",
                    "पूरे दिन केवल गुनगुना पानी ही पिएं।",
                    "खांसते-छींकते समय रूमाल या कोहनी का इस्तेमाल करें ताकि परिवार के अन्य सदस्य सुरक्षित रहें।"
                ],
                "what_not_to_do": [
                    "फ्रिज का ठंडा पानी, कोल्ड ड्रिंक या बर्फ का सेवन बिल्कुल न करें।",
                    "सीधे कूलर या एसी की सीधी ठंडी हवा में न बैठें।",
                    "धूल, मिट्टी, चूल्हे के धुएं या कीटनाशक छिड़काव के संपर्क में न आएं।",
                    "साधारण वायरल जुकाम में तुरंत मेडिकल स्टोर से एंटीबायोटिक्स न खरीदें।"
                ],
                "diet_to_eat": [
                    "अदरक, तुलसी, काली मिर्च और हल्की लौंग का काढ़ा (शहद या गुड़ के साथ)।",
                    "गुनगुना मूंग दाल का सूप और पतली खिचड़ी।",
                    "रात को सोते समय आधा चम्मच हल्दी वाला गर्म दूध।",
                    "संतरे, आंवला या अमरूद (विटामिन C रोग प्रतिरोधक क्षमता बढ़ाता है)।"
                ],
                "diet_to_avoid": [
                    "आइसक्रीम, पेस्ट्री, ठंडी दही या रात में केला।",
                    "तले हुए समोसे, पकोड़े, चिप्स और खट्टी चीजें।",
                    "धूम्रपान (बीड़ी/सिगरेट) कतई न करें।"
                ],
                "activity_and_work_guidance": [
                    "सुरक्षित कार्य: घर के हल्के काम करें; पर्याप्त आराम लें।",
                    "वर्जित शारीरिक श्रम: खेत में धूल भरी कटाई/थ्रेशिंग का काम, भारी वजन उठाना या ठंडी रात में बाहर रहना टालें।"
                ],
                "red_flag_warnings": [
                    "सांस फूलना, सीने में घरघराहट या पसलियां चलना।",
                    "खांसी में खून आना।",
                    "तेज बुखार जो 3 दिन बाद भी न उतरे।"
                ]
            }
        else:
            return {
                "condition_detected": "Cough, Common Cold & Pharyngitis",
                "what_to_do": [
                    "Gargle with warm saline water 2-3 times daily to reduce throat inflammation.",
                    "Perform plain steam inhalation for 5-10 minutes to clear congested airways.",
                    "Sip lukewarm water throughout the day.",
                    "Cover nose and mouth with a clean cloth when coughing or sneezing."
                ],
                "what_not_to_do": [
                    "Avoid drinking refrigerated or ice-cold liquids.",
                    "Avoid direct blast from air-conditioners or evaporative room coolers.",
                    "Avoid exposure to chulha wood smoke, grain dust, and passive tobacco smoke.",
                    "Do NOT start self-prescribed antibiotics for standard viral colds."
                ],
                "diet_to_eat": [
                    "Warm ginger, tulsi, and black pepper tea with raw honey.",
                    "Warm moong dal soup and vegetable broth.",
                    "Warm turmeric milk (Golden Milk) before bedtime.",
                    "Amla, oranges, and seasonal citrus rich in Vitamin C."
                ],
                "diet_to_avoid": [
                    "Chilled desserts, ice creams, cold curd, and nighttime bananas.",
                    "Greasy, deep-fried snacks and overly sour tamarind preparations.",
                    "Tobacco smoke and alcohol."
                ],
                "activity_and_work_guidance": [
                    "Permitted Work: Light indoor work, desk chores, and household supervision.",
                    "Physical Exertion to AVOID: Agricultural threshing in dusty fields, heavy labor in cold morning winds, or intense aerobic workouts."
                ],
                "red_flag_warnings": [
                    "Shortness of breath, wheezing, or chest tightness.",
                    "Hemoptysis (coughing up blood).",
                    "High fever persisting beyond 3 continuous days."
                ]
            }

    # DEFAULT / GENERAL PREVENTIVE CARE
    if language == "hi":
        return {
            "condition_detected": "सामान्य स्वास्थ्य परामर्श एवं प्रारंभिक सावधानी (General Health Precaution)",
            "what_to_do": [
                "दिनभर में 2.5 से 3 लीटर स्वच्छ, छना हुआ पानी पिएं।",
                "प्रतिदिन 7 से 8 घंटे की नियमित नींद लें।",
                "भोजन समय पर करें और सुबह 20-30 मिनट हल्का व्यायाम या पैदल चलें।"
            ],
            "what_not_to_do": [
                "बिना डॉक्टर की सलाह के मेडिकल स्टोर से गोलियां खरीदकर न खाएं।",
                "तंबाकू, बीड़ी, सिगरेट और शराब से पूर्ण दूरी बनाए रखें।"
            ],
            "diet_to_eat": [
                "घर का बना ताजा, पौष्टिक भोजन: हरी सब्जियां, दालें, रोटी और मौसमी फल।",
                "दूध, छाछ और अंकुरित अनाज।"
            ],
            "diet_to_avoid": [
                "बाजार का खुला, तला-भुना और बासी भोजन।"
            ],
            "activity_and_work_guidance": [
                "सुरक्षित कार्य: नियमित दैनिक दिनचर्या और काम जारी रखें; शरीर के संकेतों का सम्मान करें।"
            ],
            "red_flag_warnings": [
                "यदि लक्षण 2-3 दिन में ठीक न हों या बढ़ें, तो तुरंत डॉक्टर से परामर्श लें।"
            ]
        }
    else:
        return {
            "condition_detected": "General Preventive Care & Early Health Precaution",
            "what_to_do": [
                "Stay well hydrated with 2.5 to 3 liters of clean water daily.",
                "Maintain 7-8 hours of regular, restful sleep.",
                "Eat freshly cooked meals and practice 20-30 minutes of daily brisk walking."
            ],
            "what_not_to_do": [
                "Avoid over-the-counter self-medication.",
                "Refrain from all tobacco, smoking, and alcohol use."
            ],
            "diet_to_eat": [
                "Nutrient-dense home cooked meals: leafy vegetables, lentils, whole grains, seasonal fruits.",
                "Buttermilk, milk, and sprouted legumes."
            ],
            "diet_to_avoid": [
                "Deep-fried, stale, or roadside street foods."
            ],
            "activity_and_work_guidance": [
                "Permitted Work: Maintain active daily routine within personal comfort limits."
            ],
            "red_flag_warnings": [
                "Consult an authorized doctor if symptoms do not improve within 48-72 hours."
            ]
        }


def generate_chronic_care_lifestyle_plan(conditions: str, medications: List[str] = None, language: str = "hi") -> Dict[str, Any]:
    """
    Generates tailored post-consultation / disease detection lifestyle, dietary,
    and work guidance for chronic conditions (Hypertension, Diabetes, Cardiac, Anemia, Asthma).
    """
    cond_lower = (conditions or "").lower()
    meds_str = ", ".join(medications or [])

    # 1. HYPERTENSION / HIGH BP
    if any(k in cond_lower for k in ["hypertension", "bp", "blood pressure", "high blood pressure"]):
        if language == "hi":
            return {
                "condition_title": "उच्च रक्तचाप (Hypertension) आहार व कार्य प्रोटोकॉल",
                "dietary_recommendations": [
                    "नमक की मात्रा अत्यधिक कम रखें (दिनभर में 1 छोटे चम्मच यानी 5 ग्राम से भी कम)।",
                    "पोटैशियम युक्त आहार लें: ताजी लौकी, तोरई, पालक, केला और नारियल पानी।",
                    "लहसुन की 1-2 कलियां सुबह खाली पेट चबाना रक्तचाप नियंत्रण में मदद करता है।",
                    "पतली छाछ, उबली दालें और साबुत अनाज (ज्वार, बाजरा) का सेवन करें।"
                ],
                "dietary_restrictions": [
                    "अचार, पापड़, नमकीन, भुजिया और पैकेट बंद चिप्स कतई न खाएं (इनमें अत्यधिक सोडियम होता है)।",
                    "खाने में ऊपर से अतिरिक्त कच्चा नमक छिड़कना पूरी तरह बंद करें।",
                    "वनस्पति घी, डालडा और बार-बार गर्म किया गया तेल बिल्कुल न खाएं।",
                    "बीड़ी, तंबाकू और शराब से पूर्ण दूरी रखें — ये रक्त नलिकाओं को सिकोड़ते हैं।"
                ],
                "work_recommendations": [
                    "दैनिक काम: सामान्य कृषि निगरानी, दुकान या दफ्तर का काम आराम से करें।",
                    "शारीरिक गतिविधि: प्रतिदिन सुबह या शाम 30-40 मिनट समतल जमीन पर तेज चाल में टहलें (Brisk Walking)।",
                    "तनाव मुक्त रहने के लिए 15 मिनट प्राणायाम या ध्यान करें।"
                ],
                "work_restrictions": [
                    "भारी कृषि बोरियां (50 किग्रा गेहूं/खाद) या पानी के भारी ड्रम अकेले सिर पर न उठाएं।",
                    "कड़क भरी दुपहरी की तेज धूप में लगातार फावड़ा चलाने या भारी खुदाई से बचें।",
                    "अचानक बहुत तेज दौड़ना या भारी वजन उठाने वाले व्यायाम न करें।"
                ],
                "medicine_adherence_tips": [
                    "रक्तचाप की दवा (जैसे Amlodipine/Telmisartan) रोजाना सुबह एक ही निश्चित समय पर लें।",
                    "दवा कभी भी अपनी मर्जी से बंद न करें, भले ही आप पूरी तरह स्वस्थ महसूस कर रहे हों।"
                ],
                "warning_signs": [
                    "सीने में भारीपन, सिर में तेज चक्कर, अचानक धुंधला दिखना या उल्टी आना।",
                    "ऐसे लक्षण दिखते ही तुरंत नजदीकी अस्पताल में बीपी चेक कराएं।"
                ],
                "disclaimer": "यह आहार व कार्य परामर्श निर्णय-सहायता और निवारक स्वास्थ्य के लिए है। कृपया अपने डॉक्टर के निर्देशों का पालन करें।"
            }
        else:
            return {
                "condition_title": "Hypertension (High Blood Pressure) Lifestyle & Work Protocol",
                "dietary_recommendations": [
                    "Strict dietary sodium restriction: Limit total salt intake to under 1 level teaspoon (5g) per day.",
                    "Eat potassium-rich foods: Bottle gourd, ridge gourd, spinach, bananas, and tender coconut water.",
                    "Consume fresh garlic cloves, oats, and whole grains (Jowar, Bajra, Millets).",
                    "Drink skimmed buttermilk and clear lentil soups."
                ],
                "dietary_restrictions": [
                    "Strictly eliminate pickles (achaar), papad, salted namkeen, and processed potato chips.",
                    "Never add raw table salt on top of salads or cooked meals.",
                    "Avoid hydrogenated vegetable oils (vanaspati), reused cooking fat, and high-fat red meats.",
                    "Zero tolerance for smoking, beedis, gutkha, and alcohol."
                ],
                "work_recommendations": [
                    "Safe Work: General farming oversight, shopkeeping, desk work, and light household chores.",
                    "Physical Activity: 30-40 minutes of daily brisk walking on level ground.",
                    "15 minutes of slow deep breathing exercises (pranayama) for autonomic balance."
                ],
                "work_restrictions": [
                    "Avoid hoisting heavy fertilizer/grain sacks (>25 kg) or water drums on the head.",
                    "Avoid continuous heavy pickaxe/spade digging under intense midday sun.",
                    "Avoid sudden strenuous isometric straining."
                ],
                "medicine_adherence_tips": [
                    "Take prescribed antihypertensives (e.g. Amlodipine) consistently at the same hour every morning.",
                    "Never skip doses simply because you feel symptom-free; hypertension is often silent."
                ],
                "warning_signs": [
                    "Chest tightness, severe occipital headache, sudden vision blurring, or epistaxis (nosebleeds).",
                    "Rush to the nearest CHC/hospital for emergency blood pressure assessment."
                ],
                "disclaimer": "This lifestyle protocol is for clinical decision support. Must be validated by the treating physician."
            }

    # 2. DIABETES MELLITUS / SUGAR
    if any(k in cond_lower for k in ["diabet", "sugar", "t2d", "madhumeh"]):
        if language == "hi":
            return {
                "condition_title": "मधुमेह (Type 2 Diabetes) आहार व शारीरिक कार्य प्रोटोकॉल",
                "dietary_recommendations": [
                    "मोटे अनाज खाएं: गेहूं की जगह चोकरदार आटा, ज्वार, बाजरा, रागी और मेथी की रोटियां।",
                    "सब्जियां: करेला, मेथी, लौकी, खीरा, टमाटर और हरी पत्तेदार सब्जियां भरपूर खाएं।",
                    "सुबह खाली पेट 1 चम्मच भीगी मेथी का पानी या जामुन की गुठली का चूर्ण लें।",
                    "दालें, अंकुरित मूंग/चना और भुने चने खाएं।"
                ],
                "dietary_restrictions": [
                    "सफेद चीनी, गुड़, शहद, मिठाइयां (गुलाब जामुन, जलेबी) और मीठी चाय पूरी तरह बंद करें।",
                    "आलू, अरबी, शकरकंद और अधिक सफेद चावल का सेवन सीमित करें।",
                    "बाजार के पैकेट बंद बिस्कुट, केक और फ्रूट जूस न पिएं (ये शुगर को तेजी से बढ़ाते हैं)।"
                ],
                "work_recommendations": [
                    "सक्रिय दिनचर्या रखें: भोजन के बाद 20-30 मिनट अवश्य टहलें।",
                    "खेत में या घर में नियमित मध्यम स्तर का काम करते रहें — शारीरिक श्रम से इंसुलिन बेहतर काम करता है।"
                ],
                "work_restrictions": [
                    "नंगे पैर खेत में या कंकड़-पत्थर पर कतई न चलें (डायबिटीज में पैर के घाव जल्दी नहीं भरते — हमेशा मुलायम जूते/चप्पल पहनें)।",
                    "बिना खाए बहुत देर तक भारी मजदूरी न करें; जेब में हमेशा 2 टॉफी या ग्लूकोज रखें (लो शुगर से बचने के लिए)।"
                ],
                "medicine_adherence_tips": [
                    "शुगर की दवा (जैसे Metformin) डॉक्टर के निर्देशानुसार भोजन से ठीक पहले या बाद में लें।",
                    "अचानक पसीना आना, हाथ कांपना या घबराहट होना 'लो शुगर' का लक्षण है; तुरंत मीठा खाएं।"
                ],
                "warning_signs": [
                    "पैर में चोट लगना, सुन्नपन होना या घाव का न भरना।",
                    "अचानक बहुत ज्यादा प्यास लगना और बार-बार पेशाब आना।"
                ],
                "disclaimer": "शुगर की दवा और आहार में कोई भी बड़ा बदलाव अपने डॉक्टर की निगरानी में ही करें।"
            }
        else:
            return {
                "condition_title": "Type 2 Diabetes Mellitus Lifestyle & Work Protocol",
                "dietary_recommendations": [
                    "Consume complex carbohydrates and high-fiber millets: Jowar, Bajra, Ragi, and bran wheat.",
                    "Liberal intake of bitter gourd (karela), fenugreek (methi), cucumbers, and leafy greens.",
                    "Soaked fenugreek seeds in the morning and sprouted lentils (moong/chana).",
                    "High-protein plant sources: Lentils, roasted gram (bhuna chana), and boiled eggs."
                ],
                "dietary_restrictions": [
                    "Strictly avoid refined sugars, jaggery, honey, Indian sweets (mithai), and sweetened tea.",
                    "Limit starchy tubers: Potatoes, colocasia (arbi), and excessive polished white rice.",
                    "Avoid commercial packaged biscuits, bakery confectioneries, and commercial fruit juices."
                ],
                "work_recommendations": [
                    "Maintain an active daily routine: 30-45 minutes of brisk walking after meals.",
                    "Regular moderate agricultural or occupational activity improves cellular insulin sensitivity."
                ],
                "work_restrictions": [
                    "NEVER walk barefoot in agricultural fields or rocky ground (high risk of diabetic foot ulcers; always wear protective footwear).",
                    "Avoid prolonged exhausting labor on an empty stomach; always keep glucose candies handy for sudden hypoglycemia."
                ],
                "medicine_adherence_tips": [
                    "Take oral antidiabetics (e.g. Metformin) with or immediately after meals as directed.",
                    "Recognize hypoglycemia: Cold sweats, tremors, and dizziness require immediate ingestion of fast-acting sugar."
                ],
                "warning_signs": [
                    "Non-healing foot sores, peripheral numbness/tingling, or blurry vision.",
                    "Extreme polydipsia (excessive thirst) or polyuria (frequent urination)."
                ],
                "disclaimer": "Medication dosing and dietary plans must be individualized by your primary physician."
            }

    # 3. CARDIAC / ANGINA / HEART DISEASE
    if any(k in cond_lower for k in ["angina", "heart", "cardiac", "coronary", "cad", "chest"]):
        if language == "hi":
            return {
                "condition_title": "हृदय स्वास्थ्य व एंजाइना (Cardiac Care) आहार व कार्य प्रोटोकॉल",
                "dietary_recommendations": [
                    "कम तेल में उबली या भाप में पकी मौसमी हरी सब्जियां खाएं।",
                    "अलसी के बीज (Flax seeds), अखरोट और फाइबर युक्त चोकरदार दलिया लें।",
                    "अनार, पपीता और सेब जैसे ताजे फल हृदय के लिए लाभकारी हैं।"
                ],
                "dietary_restrictions": [
                    "डालडा, वनस्पति घी, मक्खन और तली हुई पूरियां/कचौरी पूरी तरह बंद करें।",
                    "अधिक नमक और ट्रांस-फैट युक्त बेकरी उत्पाद न खाएं।",
                    "बीड़ी, सिगरेट, खैनी और शराब को तुरंत त्यागें — यह जीवन रक्षक नियम है।"
                ],
                "work_recommendations": [
                    "समतल जमीन पर धीमी गति से 15-20 मिनट टहलना सुरक्षित है।",
                    "हल्के घरेलू काम, बैठने वाली दुकानदारी या लिखा-पढ़ी का काम आराम से करें।"
                ],
                "work_restrictions": [
                    "भारी वजन उठाना, तेज सीढ़ियां चढ़ना या भारी बोरी खींचना पूर्णतः वर्जित है।",
                    "कड़कड़ाती ठंड की सुबह बिना गर्म कपड़ों के बाहर निकलने से बचें (ठंड से दिल की नसें सिकुड़ती हैं)।",
                    "मानसिक तनाव और अचानक तेज गुस्से से बचें।"
                ],
                "medicine_adherence_tips": [
                    "हृदय की दवाएं (जैसे Atorvastatin, Aspirin) रोजाना बिना नागा लें।",
                    "आपातकालीन सॉरबिट्रेट (Sorbitrate) गोली हमेशा अपनी जेब में रखें।"
                ],
                "warning_signs": [
                    "सीने में बेचैनी, जो बाएं हाथ, गले या पीठ की तरफ फैले।",
                    "हल्के चलने पर भी तेज सांस फूलना या पसीना छूटना — तुरंत 112 डायल करें।"
                ],
                "disclaimer": "सीने में किसी भी नए दर्द को गैस का दर्द न समझें; तुरंत ईसीजी कराएं।"
            }
        else:
            return {
                "condition_title": "Cardiac Health & Angina Lifestyle & Work Protocol",
                "dietary_recommendations": [
                    "Steamed or boiled seasonal vegetables prepared with minimal cold-pressed oil.",
                    "Soluble fiber rich oats, flaxseeds, walnuts, and lentils.",
                    "Antioxidant-rich fruits: Pomegranate, papaya, and apples."
                ],
                "dietary_restrictions": [
                    "Strictly avoid saturated fats, dalda, hydrogenated shortening, and deep-fried foods.",
                    "Eliminate high-sodium processed foods and bakery shortenings.",
                    "Complete cessation of all tobacco, beedis, and alcohol."
                ],
                "work_recommendations": [
                    "Safe gentle walking on level terrain for 15-20 minutes daily.",
                    "Light sedentary work, shopkeeping, and indoor supervisory tasks."
                ],
                "work_restrictions": [
                    "Avoid hauling heavy loads, fast stair climbing, or pulling heavy agricultural plows.",
                    "Avoid stepping outdoors into freezing morning cold without adequate warm layers.",
                    "Avoid severe emotional distress and acute isometric straining."
                ],
                "medicine_adherence_tips": [
                    "Strict adherence to cardioprotective agents (Statins, Antiplatelets) without missing doses.",
                    "Keep emergency sublingual nitrates accessible as prescribed."
                ],
                "warning_signs": [
                    "Substernal chest pressure radiating to left shoulder, arm, neck, or back.",
                    "Dyspnea on minimal exertion or cold diaphoresis (call 112 immediately)."
                ],
                "disclaimer": "Never attribute unexplained chest discomfort to simple gas; obtain clinical ECG confirmation."
            }

    # 4. GENERAL CHRONIC PROTOCOL
    if language == "hi":
        return {
            "condition_title": f"{conditions or 'दीर्घकालिक'} स्वास्थ्य व जीवनशैली प्रोटोकॉल",
            "dietary_recommendations": [
                "ताजा, घर का बना सादा भोजन लें जिसमें दाल, रोटी और हरी सब्जियां शामिल हों।",
                "पर्याप्त मात्रा में पानी पिएं और मौसमी फल खाएं।"
            ],
            "dietary_restrictions": [
                "बाजार का तला-भुना, अत्यधिक मसालेदार या बासी भोजन न खाएं।",
                "तंबाकू, धूम्रपान और शराब से पूरी तरह दूर रहें।"
            ],
            "work_recommendations": [
                "नियमित दिनचर्या बनाए रखें; प्रतिदिन 30 मिनट हल्का व्यायाम या पैदल चलें।"
            ],
            "work_restrictions": [
                "अत्यधिक थका देने वाला शारीरिक श्रम और बिना आराम किए लगातार काम करने से बचें।"
            ],
            "medicine_adherence_tips": [
                "डॉक्टर द्वारा लिखी गई दवाएं समय पर लें और जांच की तारीख न भूलें।"
            ],
            "warning_signs": [
                "लक्षण बिगड़ने पर तुरंत अपने आशा कार्यकर्ता या डॉक्टर से संपर्क करें।"
            ],
            "disclaimer": "यह मार्गदर्शन स्वास्थ्य सुधार और प्रारंभिक सावधानी के लिए है।"
        }
    else:
        return {
            "condition_title": f"{conditions or 'Chronic Health'} Management Protocol",
            "dietary_recommendations": [
                "Fresh, wholesome home-cooked meals featuring lentils, whole grains, and seasonal greens.",
                "Maintain adequate daily hydration and fresh fruit intake."
            ],
            "dietary_restrictions": [
                "Avoid ultra-processed, excessively oily, or stale street food.",
                "Complete abstinence from tobacco, smoking, and alcohol."
            ],
            "work_recommendations": [
                "Maintain an active daily routine with 30 minutes of moderate walking."
            ],
            "work_restrictions": [
                "Avoid unmitigated chronic exhaustion and unpaced heavy manual labor."
            ],
            "medicine_adherence_tips": [
                "Follow doctor's prescription timings strictly and maintain scheduled follow-ups."
            ],
            "warning_signs": [
                "Contact your assigned ASHA worker or doctor promptly if symptoms worsen."
            ],
            "disclaimer": "This guidance supports preventive wellness and does not replace in-person clinical care."
        }
