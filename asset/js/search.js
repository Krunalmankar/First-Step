let searchData = [];
 
// Fetch search index
fetch(getSearchPath())
  .then(response => response.json())
  .then(data => {
    searchData = data;
  })
  .catch(error => console.error("Search index failed to load:", error));
 
// Determine correct path automatically
function getSearchPath() {
  const depth = window.location.pathname.split("/").length - 2;
 
  if (depth <= 1) return "search-index.json";
  if (depth === 2) return "../search-index.json";
  if (depth === 3) return "../../search-index.json";
  return "search-index.json";
}
 
const searchInput = document.getElementById("searchInput");
const searchResults = document.getElementById("searchResults");
 
if (searchInput) {
  searchInput.addEventListener("input", function () {
    const query = this.value.toLowerCase().trim();
    searchResults.innerHTML = "";
 
    if (query.length < 2) {
      searchResults.style.display = "none";
      return;
    }
 
    const results = searchData.filter(item =>
      item.title.toLowerCase().includes(query) ||
      item.keywords.toLowerCase().includes(query)
    );
 
    if (results.length === 0) {
      searchResults.style.display = "none";
      return;
    }
 
    results.forEach(item => {
      const link = document.createElement("a");
      link.href = getBasePath() + item.url;
      link.textContent = item.title;
      searchResults.appendChild(link);
    });
 
    searchResults.style.display = "block";
  });
}
 
// Fix URL base path automatically
function getBasePath() {
  const path = window.location.pathname;
  const segments = path.split("/");
  const repoName = segments[1];
 
  if (repoName && path.includes(repoName)) {
    return "/" + repoName + "/";
  }
 
  return "";
}
 
