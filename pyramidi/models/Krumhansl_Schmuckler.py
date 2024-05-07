"""
Implementation of Krumhansl-Schmuckler keyfinding algorithm and MIRtoolbox
mirmode algorithm.

Lartillot, O., Toiviainen, P., & Eerola, T. (2008).
A matlab toolbox for music information retrieval.
In Data Analysis, Machine Learning and Applications:
    Proceedings of the 31st Annual Conference of the Gesellschaft für
    Klassifikation eV, Albert-Ludwigs-Universität Freiburg,
March 7–9, 2007 (pp. 261-268).
Springer Berlin Heidelberg.

Temperley, David.
Music and Probability.
MIT Press: Cambridge, Mass.; 2007. p. 85.

Krumhansl, C. L. (1990).
Cognitive foundations of musical pitch.
New York: Oxford Universitv Press.

Aarden, Bret.
Dynamic Melodic Expectancy.
Ph.D. dissertation.
School of Music, Ohio State University; 2003.

Bellman, Héctor.
"About the determination of key of a musical excerpt"
in Proceedings of Computer Music Modeling and Retrieval (CMMR):
    Pisa, Italy; 2005. pp. 187-203

Sapp, Craig Stuart.
"Key-Profile Comparisons in Key-Finding by Correlation."
International Conference on Music Perception and Cognition (ICMPC 10);
    2008, Sapporo, Japan.
"""
###############################################################################
# Third Party Imports
from scipy.stats import pearsonr, spearmanr
from scipy.spatial.distance import cosine, euclidean
###############################################################################
# Constants
PROFILES = {
    'KrumhanslKessler': {
        'major': [
            6.35,
            2.23,
            3.48,
            2.33,
            4.38,
            4.09,
            2.52,
            5.19,
            2.39,
            3.66,
            2.29,
            2.88
        ],
        'minor': [
            6.33,
            2.68,
            3.52,
            5.38,
            2.6,
            3.53,
            2.54,
            4.75,
            3.98,
            2.69,
            3.34,
            3.17
        ]
    },
    'AardenEssen': {
        'major': [
            17.7661,
            0.145624,
            14.9265,
            0.160186,
            19.8049,
            11.3587,
            0.291248,
            22.062,
            0.145624,
            8.15494,
            0.232998,
            4.95122
        ],
        'minor': [
            18.2648,
            0.737619,
            14.0499,
            16.8599,
            0.702494,
            14.4362,
            0.702494,
            18.6161,
            4.56621,
            1.93186,
            7.37619,
            1.75623
        ]
    },
    'Simple': {
        'major': [
            2.0,
            0.0,
            1.0,
            0.0,
            1.0,
            1.0,
            0.0,
            2.0,
            0.0,
            1.0,
            0.0,
            1.0
        ],
        'minor': [
            2.0,
            0.0,
            1.0,
            1.0,
            0.0,
            1.0,
            0.0,
            2.0,
            1.0,
            0.0,
            0.5,
            0.5
        ]
    },
    'BellmanBudge': {
        'major': [
            16.8,
            0.86,
            12.95,
            1.41,
            13.49,
            11.93,
            1.25, 
            20.28,
            1.8,
            8.04,
            0.62,
            10.57
        ],
        'minor': [
            18.16,
            0.69,
            12.99,
            13.34,
            1.07,
            11.15,
            1.38,
            21.07,
            7.49,
            1.53,
            0.92,
            10.21
        ]
    },
    'AlbrechtShanahan': {
        'major': [
            0.238,
            0.006,
            0.111,
            0.006,
            0.137,
            0.094,
            0.016,
            0.214,
            0.009,
            0.080,
            0.008,
            0.081
        ],
        'minor': [
            0.220,
            0.006,
            0.104,
            0.123,
            0.019,
            0.103,
            0.012,
            0.214,
            0.062,
            0.022,
            0.061,
            0.052
        ]
    },
    'TemperleyKostkaPayne': {
        'major': [
            0.748,
            0.06,
            0.488,
            0.082,
            0.67,
            0.46,
            0.096,
            0.715,
            0.104,
            0.366,
            0.057,
            0.4
        ],
        'minor': [
            0.712,
            0.084,
            0.474,
            0.618,
            0.049,
            0.46,
            0.105,
            0.747,
            0.404,
            0.067,
            0.133,
            0.33
        ]
    },
    'Gomez_MIRtoolbox': {
        'major': [
            1.561306528,
            0.839633522,
            1.192863059,
            0.758618294,
            1.415716275,
            1.030016678,
            0.87559268,
            1.536103663,
            0.841472564,
            1.214095687,
            0.723516215,
            1.133100317
        ],
        'minor': [
            1.622160758,
            0.802739839,
            1.158742943,
            1.381344982,
            0.979464974,
            1.04863697,
            0.859499276,
            1.546622579,
            1.052296601,
            1.017899086,
            1.127755566,
            0.986193469
        ]
    }
}

for profile in PROFILES:
    buffer = {}
    for key in PROFILES[profile]:
        org = PROFILES[profile][key]
        for pc in range(
            0,
            12
        ):
            buffer[str(pc) + "_" + key] = [org[(ind - pc)%12] \
                                           for (ind, val) in enumerate(org)]     
    PROFILES[profile] = buffer

SIMILARITY_METRICS = {
    'pearsonr': lambda u, v: pearsonr(u, v)[0],
    'cosine': lambda u, v: 1 - cosine(u, v),
    'euclidean': lambda u, v: 1 - euclidean(u, v),
    'spearman': lambda u, v: spearmanr(u, v)[0] 
}
###############################################################################
def get_profiles():
    """
    Get the names of key-finding profiles available in this package.
    Use to select a specific key-finding profile,
    or to loop across all profiles.

    Arguments:
        None
    
    Returns:
        Set of variables names associated with key profiles
    """
    return set([i for i in PROFILES.keys()])

###############################################################################
def get_similarity_metrics():
    """

    Arguments:
        None
    
    Returns:
        Set of variables names associated with 
    """
    return set([i for i in SIMILARITY_METRICS.keys()])

###############################################################################
def keyfinding(
    pitchDistribution: list,
    profile: str = "KrumhanslKessler",
    similarity: str = 'pearsonr'
):
    """
    """
    if not isinstance(pitchDistribution, list):
        raise TypeError(\
            "must be pitch distribution."
        )
    if profile not in PROFILES.keys():
        raise TypeError(
            "Invalid profile name"
        )
    if similarity not in SIMILARITY_METRICS.keys():
        raise TypeError("Invalid similarity metric.")
    similarity_function = SIMILARITY_METRICS[similarity]
    coefis = {}
    for key in PROFILES[profile]:
        coefis[key] = similarity_function(
            PROFILES[profile][key],
            pitchDistribution
        )
    return coefis

###############################################################################
def mirmode(
    pitchDistribution: list,
    weights: str = "KrumhanslKessler",
    method: str = "best",
    similarity: str = "pearsonr"
):
    """
    """
    if not isinstance(
        pitchDistribution,
        list
    ):
        raise TypeError(
            "coefis must be list of integers"
        )
    if weights not in PROFILES.keys():
        raise TypeError(
            "Invalid profile name"
        )
    if method not in [
        "best",
        "sum"
    ]:
        raise TypeError(
            "method must be 'best' or 'sum'."
        )
    coefis = keyfinding(
        pitchDistribution,
        profile = weights,
        similarity = similarity
    )
    if method == "best":
        max_major = max([coefis[key] for key in coefis if 'major' in key])
        max_minor = max([coefis[key] for key in coefis if 'minor' in key])
        return max_major - max_minor
    elif method == "sum":
        sum_major = sum([coefis[key] for key in coefis if 'major' in key])
        sum_minor = sum([coefis[key] for key in coefis if 'minor' in key])
        return sum_major + sum_minor

###############################################################################