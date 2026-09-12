use std::future::{ready, Future};
use std::sync::Arc;
use std::sync::atomic::{AtomicU64, Ordering};
use tokio::sync::mpsc;

#[derive(Debug)]
struct Job {
    id: u64,
    payload: Vec<u8>,
    destroyed: Arc<AtomicU64>,
}

impl Drop for Job {
    fn drop(&mut self) {
        self.destroyed.fetch_or(1 << self.id, Ordering::Relaxed);
    }
}

#[derive(Debug)]
enum Admission {
    Accepted,
    Cancelled,
    Closed,
}

async fn enqueue(
    tx: &mpsc::Sender<Job>,
    job: Job,
    cancelled: impl Future<Output = ()>,
) -> Admission {
    tokio::select! {
        biased;
        result = tx.send(job) => match result {
            Ok(()) => Admission::Accepted,
            Err(_) => Admission::Closed,
        },
        _ = cancelled => Admission::Cancelled,
    }
}

#[tokio::main(flavor = "current_thread")]
async fn main() {
    let destroyed = Arc::new(AtomicU64::new(0));
    let make_job = |id| Job {
        id,
        payload: vec![42; 16],
        destroyed: Arc::clone(&destroyed),
    };
    let (tx, mut rx) = mpsc::channel(1);
    tx.send(make_job(1)).await.unwrap();
    let result = enqueue(&tx, make_job(2), ready(())).await;
    println!("admission={result:?}");
    println!("destroyed-before-caller-recovery-bitmask={}", destroyed.load(Ordering::Relaxed));
    let first = rx.recv().await.unwrap();
    println!("queued-id={}, bytes={}", first.id, first.payload.len());
}
