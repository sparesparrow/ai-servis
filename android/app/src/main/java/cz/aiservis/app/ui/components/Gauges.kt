package cz.aiservis.app.ui.components

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import cz.aiservis.app.data.db.TelemetryEntity

@Composable
fun DashboardGauges(latest: TelemetryEntity?) {
	if (latest == null) {
		Text("No telemetry yet")
		return
	}
	Column(modifier = Modifier.fillMaxWidth()) {
		Gauge(label = "Fuel", value = latest.fuelLevel.coerceIn(0, 100), max = 100)
		Spacer(Modifier.height(8.dp))
		Gauge(label = "Coolant (°C)", value = latest.coolantTemp.coerceAtLeast(0), max = 120)
	}
}

@Composable
private fun Gauge(label: String, value: Int, max: Int) {
	Text("$label: $value / $max")
	val progress = (value.toFloat() / max.toFloat()).coerceIn(0f, 1f)
	LinearProgressIndicator(progress = progress, modifier = Modifier.fillMaxWidth())
}
