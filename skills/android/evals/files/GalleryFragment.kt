package com.example.gallery

import android.content.Context
import android.graphics.Canvas
import android.os.Bundle
import android.util.AttributeSet
import android.view.View
import androidx.fragment.app.Fragment
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch

/** Draws the colour histogram of the photo under the cursor. Fixed size in the layout (120dp x 48dp). */
class HistogramView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
) : View(context, attrs) {
    private var bins: IntArray = IntArray(64)

    fun update(newBins: IntArray) {
        bins = newBins
        invalidate()
    }

    override fun onDraw(canvas: Canvas) {
        // draws one bar per bin
    }
}

class GalleryFragment : Fragment(R.layout.fragment_gallery) {

    private lateinit var histogram: HistogramView
    private val analyzer = HistogramAnalyzer()

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        histogram = view.findViewById(R.id.histogram)

        // Recompute the histogram while the user scrubs through the photo strip.
        viewLifecycleOwner.lifecycleScope.launch(Dispatchers.Default) {
            while (isActive) {
                val bins = analyzer.histogramOf(PhotoStrip.current())
                histogram.update(bins)
                delay(100)
            }
        }
    }
}

/*
Play Console ANR cluster for this screen (Android 15, Pixel 7a), excerpt:

Subject: Input dispatching timed out (Waited 5001ms for MotionEvent)

"main" prio=5 tid=1 Native
  | group="main" sCount=1 ucsCount=0 flags=1 obj=0x72a4f0c8 self=0xb400007a1c2c3c00
  | state=S schedstat=( 1840221315 412530121 2905 ) utm=151 stm=32 core=4 HZ=100
  native: #00 pc 000a2f6c  /apex/com.android.runtime/lib64/bionic/libc.so (__epoll_pwait+12)
  native: #01 pc 00018f04  /system/lib64/libutils.so (android::Looper::pollOnce(int, int*, int*, void**)+208)
  at android.os.MessageQueue.nativePollOnce(Native method)
  at android.os.MessageQueue.next(MessageQueue.java:339)
  at android.os.Looper.loopOnce(Looper.java:179)
  at android.os.Looper.loop(Looper.java:317)
  at android.app.ActivityThread.main(ActivityThread.java:8705)

Dump taken 0.3 s after the ANR. No other thread holds a lock the main thread waits on, CPU and
memory pressure are normal, and no crash (CalledFromWrongThreadException) was ever reported.
*/
