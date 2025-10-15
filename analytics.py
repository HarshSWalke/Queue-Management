# analytics.py
import matplotlib.pyplot as plt
import io
import base64
from typing import List, Dict
import numpy as np
import time

class Analytics:
    """
    Basic stats and visualizations. This is intentionally simple —
    it uses stored service timestamps (simulated) to compute averages and peaks.
    """

    def __init__(self):
        # store timestamps (epoch seconds) of served customers for simulation and computation
        self.served_timestamps = []  # list of floats

    def record_service(self, timestamp:float=None):
        """Record that a service happened at timestamp (default now)."""
        self.served_timestamps.append(timestamp if timestamp else time.time())

    def average_wait_time(self, recorded_waits:List[float]) -> float:
        """
        Compute average wait from a list of waits (seconds).
        If empty, returns 0.
        """
        if not recorded_waits:
            return 0.0
        return float(sum(recorded_waits) / len(recorded_waits))

    def peak_hour_detection(self) -> Dict:
        """
        Return busiest hour (simulated) from served_timestamps:
        Returns dict {'hour': int (0-23), 'count': int}
        """
        if not self.served_timestamps:
            return {"hour": None, "count": 0}
        # convert to hours
        hours = [time.localtime(ts).tm_hour for ts in self.served_timestamps]
        (vals,counts) = np.unique(hours, return_counts=True)
        idx = int(np.argmax(counts))
        return {"hour": int(vals[idx]), "count": int(counts[idx])}

    def generate_ascii_graph(self, buckets:int=10) -> str:
        """
        Generate a tiny ASCII bar graph for counts per hour (0-23) aggregated into buckets.
        """
        if not self.served_timestamps:
            return "No data to display."
        hours = [time.localtime(ts).tm_hour for ts in self.served_timestamps]
        counts = [0]*24
        for h in hours:
            counts[h] += 1
        # format to string
        lines = []
        for hour in range(24):
            lines.append(f"{hour:02d}: " + "#" * counts[hour])
        return "\n".join(lines)

    def generate_matplotlib_bar(self):
        """
        Produce a PNG image (base64) of served counts per hour for Streamlit image display.
        Returns bytes data of PNG.
        """
        if not self.served_timestamps:
            # create empty plot with message
            fig, ax = plt.subplots(figsize=(8,3))
            ax.text(0.5, 0.5, "No data", ha='center', va='center', fontsize=14)
            ax.axis('off')
        else:
            hours = [time.localtime(ts).tm_hour for ts in self.served_timestamps]
            counts = [0]*24
            for h in hours:
                counts[h] += 1
            fig, ax = plt.subplots(figsize=(10,4))
            ax.bar(range(24), counts)
            ax.set_xlabel("Hour of day")
            ax.set_ylabel("Services handled")
            ax.set_title("Services per hour")
            ax.set_xticks(range(24))
        buf = io.BytesIO()
        fig.tight_layout()
        fig.savefig(buf, format='png')
        buf.seek(0)
        data = buf.read()
        plt.close(fig)
        return data
