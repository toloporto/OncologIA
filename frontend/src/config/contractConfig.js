// Dirección del contrato desplegado (OrthoData)
export const ORTHO_DATA_ADDRESS = "0x5FbDB2315678afecb367f032d93F642f64180aa3";

// ABI del contrato (Interfaz para interactuar con él)
export const ORTHO_DATA_ABI = [
  "function mintDiagnosis(address patient, string memory diagnosis, uint256 severity, string memory ipfsHash, string memory recommendations) public returns (uint256)",
  "function getMedicalData(uint256 tokenId) public view returns (tuple(string diagnosis, uint256 severity, uint256 timestamp, string ipfsHash, string recommendations, bool isPublic))",
  "function getPatientTokens(address patient) public view returns (uint256[])",
  "function ownerOf(uint256 tokenId) public view returns (address)",
  "function tokenURI(uint256 tokenId) public view returns (string memory)",
  "event DiagnosisMinted(uint256 indexed tokenId, address indexed patient, string diagnosis, uint256 severity, string ipfsHash)"
];

// Dirección del contrato de Consultas (OrthoConsult)
export const ORTHO_CONSULT_ADDRESS = "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512";

// ABI del contrato OrthoConsult (funciones principales)
export const ORTHO_CONSULT_ABI = [
  "function isRegisteredOrthodontist(address) public view returns (bool)",
  "function registerOrthodontist(address _orthoAddress) public",
  "function createCase(string memory _descriptionHash, uint256 _reward, uint256 _requiredOpinions) public payable",
  "function submitOpinion(uint256 _caseId, string memory _opinionHash) public",
  "function claimReward(uint256 _caseId) public",
  "function getOpinionsByCase(uint256 _caseId) public view returns (tuple(address orthodontist, string opinionHash, bool isQualityMarked)[])",
  "event CaseCreated(uint256 indexed caseId, address indexed patient, uint256 reward, uint256 requiredOpinions)",
  "event OpinionSubmitted(uint256 indexed caseId, address indexed orthodontist)",
  "event RewardClaimed(uint256 indexed caseId, address indexed orthodontist, uint256 amount)",
  "event OrthodontistRegistered(address indexed orthodontist)"
];

// Dirección del contrato de Mercado (OrthoMarket)
export const ORTHO_MARKET_ADDRESS = "0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0";

// ABI del contrato OrthoMarket
export const ORTHO_MARKET_ABI = [
  "function getActiveListings() public view returns (uint256[])",
  "function purchaseData(uint256 tokenId) public payable",
  "function listData(uint256 tokenId, uint256 price) public",
  "event DataListed(uint256 indexed tokenId, uint256 price)",
  "event DataPurchased(uint256 indexed tokenId, address indexed buyer, uint256 price)"
];

// Dirección del contrato de Consentimiento (OrthoConsent)
export const ORTHO_CONSENT_ADDRESS = "0x610178dA211FEF7D417bC0e6FeD39F05609AD788";

// ABI del contrato OrthoConsent
// ABI del contrato OrthoConsent
export const ORTHO_CONSENT_ABI = [
  "function grantConsent(uint256 _tokenId, address _recipient, uint8 _purpose, uint256 _durationSeconds, string memory _termsHash) public returns (bytes32)",
  "function revokeConsent(bytes32 _consentId, string memory _reason) public",
  "function checkConsent(address _patient, address _recipient, uint256 _tokenId, uint8 _purpose) public view returns (bool)",
  "function getPatientConsents(address _patient) public view returns (bytes32[])",
  "function getConsentDetails(bytes32 _consentId) public view returns (tuple(uint256 tokenId, address patient, address recipient, uint8 purpose, uint256 startTime, uint256 expirationTime, bool isValid, string termsHash))",
  "event ConsentGranted(bytes32 indexed consentId, address indexed patient, address indexed recipient, uint256 tokenId, uint8 purpose, uint256 expirationTime)",
  "event ConsentRevoked(bytes32 indexed consentId, address indexed patient, address indexed recipient, string reason)"
];
