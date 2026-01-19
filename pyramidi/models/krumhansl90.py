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
__all__ = [
    "get_key_profiles", "get_similarity_metrics", "keyfinding", "mirmode"
]

PROFILES = {
    'KrumhanslKessler': {
        'major': [
            6.35, 2.23, 3.48, 2.33, 4.38, 4.09,
            2.52, 5.19, 2.39, 3.66, 2.29, 2.88
        ],
        'minor': [
            6.33, 2.68, 3.52, 5.38, 2.6, 3.53,
            2.54, 4.75, 3.98, 2.69, 3.34, 3.17
        ]
    },
    'AardenEssen': {
        'major': [
            17.7661, 0.145624, 14.9265, 0.160186, 19.8049, 11.3587, 0.291248,
            22.062, 0.145624, 8.15494, 0.232998, 4.95122
        ],
        'minor': [
            18.2648, 0.737619, 14.0499, 16.8599, 0.702494, 14.4362, 0.702494,
            18.6161, 4.56621, 1.93186, 7.37619, 1.75623
        ]
    },
    'Simple': {
        'major': [
            2.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0.0, 2.0, 0.0, 1.0, 0.0, 1.0
        ],
        'minor': [
            2.0, 0.0, 1.0, 1.0, 0.0, 1.0, 0.0, 2.0, 1.0, 0.0, 0.5, 0.5
        ]
    },
    'BellmanBudge': {
        'major': [
            16.8, 0.86, 12.95, 1.41, 13.49, 11.93,
            1.25, 20.28, 1.8, 8.04, 0.62, 10.57
        ],
        'minor': [
            18.16, 0.69, 12.99, 13.34, 1.07, 11.15,
            1.38, 21.07, 7.49, 1.53, 0.92, 10.21
        ]
    },
    'AlbrechtShanahan': {
        'major': [
            0.238, 0.006, 0.111, 0.006, 0.137, 0.094,
            0.016, 0.214, 0.009, 0.080, 0.008, 0.081
        ],
        'minor': [
            0.220, 0.006, 0.104, 0.123, 0.019, 0.103,
            0.012, 0.214, 0.062, 0.022, 0.061, 0.052
        ]
    },
    'TemperleyKostkaPayne': {
        'major': [
            0.748, 0.06, 0.488, 0.082, 0.67, 0.46,
            0.096, 0.715, 0.104, 0.366, 0.057, 0.4
        ],
        'minor': [
            0.712, 0.084, 0.474, 0.618, 0.049, 0.46,
            0.105, 0.747, 0.404, 0.067, 0.133, 0.33
        ]
    },
    'Gomez_MIRtoolbox': {
        'major': [
            1.561306528, 0.839633522, 1.192863059, 0.758618294,
            1.415716275, 1.030016678, 0.87559268, 1.536103663,
            0.841472564, 1.214095687, 0.723516215, 1.133100317
        ],
        'minor': [
            1.622160758, 0.802739839, 1.158742943, 1.381344982,
            0.979464974, 1.04863697, 0.859499276, 1.546622579,
            1.052296601, 1.017899086, 1.127755566, 0.986193469
        ]
    }
}

for profile_name, modes in PROFILES.items():
    buffer = {}
    for mode, profile in modes.items():
        for pc in range(12):
            buffer[f"{pc}_{mode}"] = [
                profile[(i - pc) % 12]
                for i in range(12)
            ]
    PROFILES[profile_name] = buffer

SIMILARITY_METRICS = {
    'pearsonr': lambda u, v: pearsonr(u, v)[0],
    'cosine': lambda u, v: 1 - cosine(u, v),
    'euclidean': lambda u, v: 1 - euclidean(u, v),
    'spearman': lambda u, v: spearmanr(u, v)[0] 
}

###############################################################################
def get_key_profiles():
    """Get the names of key-finding profiles available in this package.

    Arguments:
    None
    
    Returns:
    set -- variables names associated with key profiles.

    """
    return set(PROFILES)

###############################################################################
def get_similarity_metrics():
    """Get the names of similarity metrics availble for Krumhansl keyfinding.

    Arguments:
    None
    
    Returns:
    set -- variables names associated with available similarity metrics.
 
    """
    return set(SIMILARITY_METRICS)

###############################################################################
def keyfinding(
    pitch_distribution: dict[int, float],
    key_profile: str = "KrumhanslKessler",
    similarity_metric: str = 'pearsonr'
):
    """Get key coefficients after Krumhansl 1990.

    Arguments:
    pitch_distribution (dict[int, float]) -- Pitch Class Distribution returned by `pyramidi.analysis.pcd()`.
    key_profile (string) -- A valid key profile: must be a value of `get_key_profiles()`.
    similarity_metric (string) -- A valid similarity metric: must be a function from `get_similarity_metrics()` or otherwise a function that can compare two sets of pcd-like values.

    Returns:
    dict[str, float] -- keys = key name, values = similarity metric.

    TODO: Allow other variables to be used for profiles/similarity.
    """
    if not isinstance(pitch_distribution, dict):
        raise TypeError(
            "must be pitch distribution as a dictionary."
        )
    if key_profile not in PROFILES:
        raise TypeError(
            "Invalid profile name"
        )
    if similarity_metric not in SIMILARITY_METRICS:
        raise TypeError(
            "Invalid similarity metric."
        )
    similarity_function = SIMILARITY_METRICS[similarity_metric]
    coefis = {}
    for key in PROFILES[key_profile]:
        coefis[key] = float(
            similarity_function(
                PROFILES[key_profile][key],
                list(pitch_distribution.values())
            )
        )
    return coefis

###############################################################################
def mirmode(
    key_coefficients: dict[str, float],
    method: str = "best"
):
    """

    Arguments:
    key_coefficients (dict[str, float]) -- Key coefficients returned by `keyfinding()`.
    method (string) -- best or sum: best subtracts the highest major and minor modes, while sum take the difference of sums for major and minor.

    Returns:
    float -- mirmode coefficient. Values closer to -1 are more minor, values closer to 1 are more major

    """
    majors = [v for k, v in key_coefficients.items() if k.endswith("major")]
    minors = [v for k, v in key_coefficients.items() if k.endswith("minor")]
    if method == "best":
        return max(majors) - max(minors)
    elif method == "sum":
        return sum(majors) + sum(minors)
    else:
        raise ValueError("Invalid method")

###############################################################################
