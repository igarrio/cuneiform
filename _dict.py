# --------------------------------------------------------------------------
# Словник логограм: англ. слова | читання | знак(и) Unicode через "+" | pos
# pos: n іменник, adj прикметник, v дієслово, pron займенник, neg заперечення
# --------------------------------------------------------------------------
LEXICON = """
king,ruler,monarch,sovereign,emperor | lugal | LUGAL | n
god,goddess,deity,divine | dingir | AN | n
sky,heaven,heavens | an | AN | n
house,home,temple,shrine,building | e2 | E2 | n
palace | e2-gal | E2+GAL | n
mouth,speech,word,voice,language | ka | KA | n
eye,sight | igi | IGI | n
hand,arm | šu | SHU | n
foot,leg | gir2 | GIR2 | n
head,top | sag | SAG | n
heart,inside,middle,interior | šag4 | SHA3 | n
blood | uš2 | USH | n
life,breath,soul | zi | ZI | n
name,fame,year | mu | MU | n
day,sun,light,daylight,dawn | ud | UD | n
star | mul | AN THREE TIMES | n
earth,ground,soil,place,floor | ki | KI | n
land,country,mountain,hill,foreign,highland | kur | KUR | n
water,liquid,flood | a | A | n
fire,flame | ne | NE | n
stone,rock,boulder | na4 | NA4 | n
tree,wood,timber,forest,plank | giš | GISH | n
reed | gi | GI | n
barley,grain,wheat,corn | še | SHE | n
bread,food,meal,ration | ninda | NINDA2 | n
milk | ga | GA | n
oil,fat,butter | i3 | I | n
silver,money,coin | ku3 | KU3 | n
ox,cow,bull,cattle | gud | GUD | n
sheep,lamb | udu | LU | n
dog,hound | ur | UR | n
snake,serpent | muš | MUSH | n
fish | ku6 | HA | n
donkey | anše | ANSHE | n
man,person,human,someone,somebody | lu2 | LU2 | n
woman,female | munus | SAL | n
child,son,boy,kid,offspring | dumu | TUR | n
daughter,girl | dumu-munus | TUR+SAL | n
father | ab-ba | AB+BA | n
brother,sibling | šeš | SHESH | n
scribe | dub-sar | DUB+SAR | n
people,nation,folk,population,crowd | un | UN | n
lord,master,owner,chief | en | EN | n
queen,lady,mistress | nin | NIN | n
servant,slave,worker | arad2 | ARAD | n
soldier,army,warrior,troops | erin2 | ERIN2 | n
city,town,village,settlement | uru | URU | n
gate,door,entrance | ka2 | KA2 | n
field,farmland,meadow | gan2 | GAN2 | n
road,way,journey,path,trip,campaign | kaskal | KASKAL | n
boat,ship,vessel | ma2 | MA2 | n
great,big,large,mighty,huge,vast,grand,important,elder | gal | GAL | adj
small,little,tiny,young,minor | tur | TUR | adj
good,sweet,pleasant,fine,nice,beautiful,happy | dug3 | KA TIMES LI | adj
i,me,my | ĝa2-e | GA2+E | pron
you,your | za-e | ZA+E | pron
not,no,never,without | nu | NU | neg
give | sum | SUM | v
go,come,walk,arrive | du | DU | v
eat,devour,consume | gu7 | KA TIMES GAR | v
drink | nag | KA TIMES A | v
see,look,watch,behold,observe | igi | IGI | v
say,speak,tell,call,declare,announce | dug4 | KA | v
know,understand,learn | zu | ZU | v
write,inscribe,record | sar | SAR | v
return | gur | GUR | v
enter | ku4 | KU4 | v
make,do,build,create,construct | ak | AK | v
"""

NUM_WORDS = {**{w: i for i, w in enumerate(
    "one two three four five six seven eight nine ten".split(), 1)},
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50}
STOPWORDS = {"a", "an", "the", "is", "are", "am", "was", "were", "be", "been",
             "of", "to", "did", "does", "will", "would"}
IRREGULAR = {"gave": "give", "given": "give", "went": "go", "gone": "go",
             "came": "come", "ate": "eat", "eaten": "eat", "saw": "see",
             "seen": "see", "said": "say", "wrote": "write", "written": "write",
             "knew": "know", "known": "know", "built": "build", "made": "make",
             "died": "die", "drank": "drink", "killed": "kill", "stood": "stand",
             "sat": "sit", "children": "child", "men": "man", "women": "woman"}
IRREG_PLURAL = {"child": "children", "man": "men", "woman": "women"}