//热门城市排行榜
async function fetchCityRankings() {
    try {
        const response = await fetch('https://api.example.com/city-rankings'); // Replace with your actual API endpoint
        const data = await response.json();
        const cityRankList = document.getElementById('city_Rank_list');
        cityRankList.innerHTML = ''; // Clear existing list

        data.rankings.forEach(city => {
            const listItem = document.createElement('li');
            listItem.textContent = city.name; // Assuming the city object has a 'name' property
            cityRankList.appendChild(listItem);
        });

        // Implementing infinite scroll for pagination
        window.addEventListener('scroll', async () => {
            if (window.innerHeight + window.scrollY >= document.body.offsetHeight) {
                // Fetch more rankings when scrolled to the bottom
                const moreData = await fetchMoreCityRankings(); // Implement this function to fetch more data
                moreData.rankings.forEach(city => {
                    const listItem = document.createElement('li');
                    listItem.textContent = city.name;
                    cityRankList.appendChild(listItem);
                });
            }
        });
    } catch (error) {
        console.error('Error fetching city rankings:', error);
    }
}