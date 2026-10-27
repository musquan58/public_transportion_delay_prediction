async function recent() {

    const t = document.getElementById("recent");

    if (!t) return;

    const r = await fetch("/api/recent");

    const d = await r.json();

    if (!d.length) {

        t.innerHTML =
            '<tr><td colspan="5">No predictions yet.</td></tr>';

        return;
    }

    t.innerHTML = d.map(x => `

        <tr>

            <td>
                <b>${x.route}</b>
            </td>

            <td>
                ${x.source} → ${x.destination}
            </td>

            <td>
                <b>${x.delay} min</b>
            </td>

            <td>

                <span class="badge ${
                    x.status == "On Time"
                    ? "bg-success"
                    : x.status == "Slight Delay"
                    ? "bg-warning text-dark"
                    : "bg-danger"
                }">

                    ${x.status}

                </span>

            </td>

            <td>
                ${x.created_at}
            </td>

        </tr>

    `).join("");
}


/* =========================================
   EXPLAINABLE DELAY PREDICTION
========================================= */

const f = document.getElementById("predictForm");


if (f) {

    f.addEventListener("submit", async e => {

        e.preventDefault();

        const button = f.querySelector("button");

        button.disabled = true;

        button.innerText = "Predicting...";


        try {

            const response = await fetch(
                "/api/predict",
                {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify(
                        Object.fromEntries(
                            new FormData(f)
                        )
                    )
                }
            );


            const data = await response.json();


            if (data.error) {

                alert(data.error);

                return;
            }


            /* Show result */

            document
                .getElementById("result")
                .classList.remove("d-none");


            /* Delay */

            document
                .getElementById("delay")
                .innerText = data.delay;


            /* Route */

            document
                .getElementById("resultRoute")
                .innerText =
                "ROUTE " + data.route;


            /* Journey */

            document
                .getElementById("resultJourney")
                .innerText =
                data.source + " → " +
                data.destination;


            /* Status */

            const status =
                document.getElementById("status");

            status.innerText = data.status;


            /* Status color */

            if (data.status === "On Time") {

                status.style.background = "#dcfce7";

                status.style.color = "#166534";

            }

            else if (data.status === "Slight Delay") {

                status.style.background = "#fef3c7";

                status.style.color = "#92400e";

            }

            else {

                status.style.background = "#fee2e2";

                status.style.color = "#991b1b";

            }


            /* =====================================
               DISPLAY EXPLANATION FACTORS
            ===================================== */

            const factorList =
                document.getElementById("factorList");


            factorList.innerHTML = "";


            data.factors.forEach(factor => {

                const factorHTML = `

                    <div class="factor-item">

                        <div class="factor-left">

                            <span class="factor-icon">
                                ${factor.icon}
                            </span>

                            <span>
                                ${factor.name}
                            </span>

                        </div>


                        <strong>
                            +${factor.impact} min
                        </strong>

                    </div>

                `;


                factorList.innerHTML += factorHTML;

            });


            /* Recommendation */

            const recommendation =
                document.getElementById(
                    "recommendation"
                );


            if (data.status === "Major Delay") {

                recommendation.innerText =
                    "Consider traveling outside peak hours or choosing an alternative route.";

            }

            else if (data.status === "Slight Delay") {

                recommendation.innerText =
                    "A small delay is expected. Allow some extra travel time.";

            }

            else {

                recommendation.innerText =
                    "The route is currently expected to operate close to schedule.";

            }


            /* Scroll to result */

            document
                .getElementById("result")
                .scrollIntoView({
                    behavior: "smooth"
                });

        }


        catch (error) {

            alert(
                "Unable to connect to prediction server."
            );

        }


        finally {

            button.disabled = false;

            button.innerText =
                "🔮 Predict Delay";

        }

    });

}


/* =========================================
   STATISTICS
========================================= */

async function charts() {

    const statusCanvas =
        document.getElementById("statusChart");

    const trafficCanvas =
        document.getElementById("trafficChart");


    if (!statusCanvas) return;


    const response =
        await fetch("/api/stats");


    const data =
        await response.json();


    new Chart(

        statusCanvas,

        {

            type: "doughnut",

            data: {

                labels:
                    Object.keys(data.status),

                datasets: [

                    {

                        data:
                            Object.values(data.status)

                    }

                ]

            }

        }

    );


    new Chart(

        trafficCanvas,

        {

            type: "bar",

            data: {

                labels:
                    Object.keys(data.traffic),

                datasets: [

                    {

                        label:
                            "Predictions",

                        data:
                            Object.values(
                                data.traffic
                            )

                    }

                ]

            },

            options: {

                scales: {

                    y: {

                        beginAtZero: true

                    }

                }

            }

        }

    );

}


recent();

charts();

/* =========================================
   ADVANCED ANALYTICS
========================================= */

async function loadAdvancedAnalytics() {

    const routeChart =
        document.getElementById("routeChart");

    const weatherChart =
        document.getElementById("weatherChart");

    const totalTrips =
        document.getElementById("totalTrips");


    // Only run on Statistics page

    if (!routeChart || !totalTrips) {
        return;
    }


    try {

        const response =
            await fetch("/api/analytics");

        const data =
            await response.json();


        /* KPI VALUES */

        document.getElementById(
            "totalTrips"
        ).innerText =
            data.summary.total;


        document.getElementById(
            "onTimeRate"
        ).innerText =
            data.summary.on_time_percentage + "%";


        document.getElementById(
            "avgDelay"
        ).innerText =
            data.summary.avg_delay + " min";


        document.getElementById(
            "majorDelays"
        ).innerText =
            data.summary.major_delays;


        /* ROUTE CHART */

        new Chart(

            routeChart,

            {

                type: "bar",

                data: {

                    labels:
                        data.routes.map(
                            x => "Route " + x.route
                        ),

                    datasets: [

                        {

                            label:
                                "Average Delay (min)",

                            data:
                                data.routes.map(
                                    x => x.avg_delay
                                )

                        }

                    ]

                },

                options: {

                    responsive: true,

                    scales: {

                        y: {

                            beginAtZero: true

                        }

                    }

                }

            }

        );


        /* WEATHER CHART */

        new Chart(

            weatherChart,

            {

                type: "bar",

                data: {

                    labels:
                        data.weather.map(
                            x => x.weather
                        ),

                    datasets: [

                        {

                            label:
                                "Average Delay (min)",

                            data:
                                data.weather.map(
                                    x => x.avg_delay
                                )

                        }

                    ]

                },

                options: {

                    responsive: true,

                    scales: {

                        y: {

                            beginAtZero: true

                        }

                    }

                }

            }

        );


        /* AUTOMATIC INSIGHT */

        let message =
            "The system analysed " +
            data.summary.total +
            " predictions.";


        if (data.routes.length > 0) {

            const worstRoute =
                data.routes[0];

            message +=
                " Route " +
                worstRoute.route +
                " currently has the highest average delay of " +
                worstRoute.avg_delay +
                " minutes.";

        }


        document.getElementById(
            "insightText"
        ).innerText = message;


    } catch (error) {

        console.error(
            "Analytics error:",
            error
        );

    }

}


loadAdvancedAnalytics();

// =====================================
// MANUAL ROUTE VISUALIZATION
// =====================================

function showRouteVisualization() {

    const routeInput = document
        .getElementById("routeNumberInput")
        .value
        .trim();

    const routes = {

        "101": {
            stops: ["Central", "Market", "University", "Airport"]
        },

        "202": {
            stops: ["Central", "University", "Airport", "Terminal"]
        },

        "303": {
            stops: ["Central", "Mall", "Market", "Airport"]
        },

        "404": {
            stops: ["Central", "Station", "University", "Airport"]
        },

        "505": {
            stops: [ "College", "central","university","Home"]
        },

        "606": {
            stops: ["Central", "Market", "College", "Terminal"]
        }

    };

    // Check whether route exists
    if (!routes[routeInput]) {

        alert(
            "Route " + routeInput +
            " is not available.\n\n" +
            "Available routes: 101, 202, 303, 404, 505, 606"
        );

        return;
    }

    const selectedRoute = routes[routeInput];

    // Change route number
    document.getElementById("visualRouteName").textContent =
        "Route " + routeInput;

    document.getElementById("visualRoute").textContent =
        routeInput;

    // Change stops
    document.getElementById("stop1").textContent =
        selectedRoute.stops[0];

    document.getElementById("stop2").textContent =
        selectedRoute.stops[1];

    document.getElementById("stop3").textContent =
        selectedRoute.stops[2];

    document.getElementById("stop4").textContent =
        selectedRoute.stops[3];
}

// =========================
// DARK MODE
// =========================

function toggleDarkMode() {
    document.body.classList.toggle("dark-mode");

    const isDark = document.body.classList.contains("dark-mode");

    localStorage.setItem("darkMode", isDark ? "enabled" : "disabled");

    const button = document.getElementById("darkModeBtn");

    if (button) {
        button.innerHTML = isDark ? "☀️ Light Mode" : "🌙 Dark Mode";
    }
}

// Load saved dark mode setting
document.addEventListener("DOMContentLoaded", function () {

    const savedMode = localStorage.getItem("darkMode");
    const button = document.getElementById("darkModeBtn");

    if (savedMode === "enabled") {
        document.body.classList.add("dark-mode");

        if (button) {
            button.innerHTML = "☀️ Light Mode";
        }
    }

});