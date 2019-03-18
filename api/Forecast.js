const Forecast = require('forecast-promise');
const forecast = new Forecast({
    accountId: '974183',
    token: '1876053.pt.Jnvx30oYxpfQIGrIafVbsB2SS83YMX7tyu0XbcrtEUQ7_4X_F9kx3HyAKLji3OsRd2zT4rA6jQJ8cDBqRpnMEw',
});

forecast.people().then(people => {
    console.log(people);
});

//forecast.assignments().then(assignments => {
//    console.log(assignments);
//});
